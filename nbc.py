from common import *
import math
import re

class Factory(CommandModuleFactory):
	def Commands(self):
		return {
			'bayestrigger':BayesTrigger(),
			'bayesconfig':BayesConfig(),
			'bayestrainer':BayesTrainer()
		}
	def Defaults(self):
		return {
			"nbcTriggerChance":5
		}


class BayesConfig(BotCommand):

	def __init__(self):
		self._thresholdRX = re.compile(r"set\sthreshold\sfor\s(nbc\s)?['\"]?(?P<name>\w+)['\"]?\sto\s(?P<value>0\.[0-9]+)",re.IGNORECASE) #'set threshold for <name> to 0.xxx'
		self._setTriggerRX = re.compile(r"(?P<mode>add|remove)\strigger\s(['\"]?(?P<trigger>\w+)['\"]?)\sto\s(nbc\s)?(?P<name>\w+)",re.IGNORECASE)
		self._addRX = re.compile(r"create\snbc\s['\"]?(?P<name>\w+)['\"]?(\strigger\s['\"]?(?P<trigger>\w+)['\"]?)?",re.IGNORECASE)

	def Try(self,bot,query):
		res = None
		if query.Directed():
			if len(bot.getCommand("bayestrigger")._classifiers) == 0:
				bot.getCommand("bayestrigger")._getClassifiers(bot)

			
			if self._thresholdRX.match(query.Message()):
				_match = self._thresholdRX.match(query.Message())
				bot.sql(r"update pail_nbcconfig set threshold=%s where nbcname=%s",(_match.group("value"),_match.group("name")))
				bot.getCommand("bayestrigger")._getClassifiers(bot)
				self.OK(bot,query)
				res = self.Handled("%(who)s changed threshold for %(nbc)s to %(value)s"%{'who':nm_to_n(query.From()),'nbc':_match.group("name"),'value':_match.group("value")})

			elif self._setTriggerRX.match(query.Message()):
				_match = self._setTriggerRX.match(query.Message())
				mode = ""
				triggers = bot.getCommand("bayestrigger")._classifiers[_match.group("name")]["triggers"]
				if not _match.group("trigger") in triggers and _match.group("mode") == "add":
					triggers.append(_match.group("trigger"))
					mode="added"
				elif _match.group("trigger") in triggers and _match.group("mode") == "remove":
					triggers.remove(_match.group("trigger"))
					mode = "removed"
				else:
					return self.Unhandled()
				tstr = ';'.join(triggers)
				bot.sql(r"update pail_nbcconfig set triggers=%s where nbcname=%s",(tstr,_match.group("name")))
				bot.getCommand("bayestrigger")._getClassifiers(bot)
				self.OK(bot,query)
				res = self.Handled("%(who)s %(mode)s '%(trigger)s' as a trigger for %(nbc)s"%{'who':nm_to_n(query.From()),'nbc':_match.group("name"),'trigger':_match.group("trigger"),'mode':mode})
			
			elif self._addRX.match(query.Message()):
				_match = self._addRX.match(query.Message())
				trigger = _match.group("trigger")
				if trigger is None:
					trigger = ""
				bot.sql(r"insert into pail_nbcconfig values (%s, 2.0, %s);",(_match.group("name"),trigger))
				bot.getCommand("bayestrigger")._getClassifiers(bot)
				self.OK(bot,query)
				res = self.Handled("%(who)s created nbc %(nbc)s"%{'who':nm_to_n(query.From()),'nbc':_match.group("name")})
				
		if res is None:
			return self.Unhandled()
		else:
			return res

	def RequiresAdmin(self):
		return True

class BayesTrainer(BotCommand):

	def __init__(self):
		self._posRX = re.compile("(that\swas\s(good|right)|well\sdone|good|\+\+|\+)",re.IGNORECASE)
		self._negRX = re.compile("(that\swas\s(wrong|bad)|-|--)",re.IGNORECASE)
		self._trainRX = re.compile("train\s(nbc\s)?['\"]?(?P<name>\w+)['\"]?\s(?P<mode>pos(itive)?|neg(itive)?|-|\+)\swith\s['\"](?P<data>[^'\"]*)['\"]",re.IGNORECASE)

	def Try(self,bot,query):
		trigger = bot.getCommand("bayestrigger")
		if len(trigger._classifiers) == 0:
			trigger._getClassifiers(bot)
		if query.Directed():
			if self._posRX.match(query.Message()) and trigger._last != "" and trigger._lastClassifier != "":
				_match = self._posRX.match(query.Message())
				bot.sql("insert into pail_nbcdata values (0, %s , %s, %s)",(trigger._lastClassifier,"pos",trigger._last))
				trigger._cObj[trigger._lastClassifier].invalidateCache()
				return self.Handled("%(who)s added positive data '%(data)s' to nbc %(name)s"%{'who':nm_to_n(query.From()),'data':trigger._last,'name':trigger._lastClassifier})
			elif self._negRX.match(query.Message()) and trigger._last != "" and trigger._lastClassifier != "":
				_match = self._negRX.match(query.Message())
				bot.sql("insert into pail_nbcdata values (0, %s , %s, %s)",(trigger._lastClassifier,"neg",trigger._last))
				trigger._cObj[trigger._lastClassifier].invalidateCache()
				return self.Handled("%(who)s added negitive data '%(data)s' to nbc %(name)s"%{'who':nm_to_n(query.From()),'data':trigger._last,'name':trigger._lastClassifier})
			elif self._trainRX.match(query.Message()) and isAdmin(query.From()):
				_match = self._trainRX.match(query.Message())
				if _match.group("mode").lower()[:3] == "pos" or _match.group("mode")[0] == "+":
					mode = "pos"
				else:
					mode = "neg"
				bot.sql("insert into pail_nbcdata values (0, %s , %s, %s)",(_match.group("name"),mode,_match.group("data")))
				trigger._cObj[_match.group("name")].invalidateCache()
				return self.Handled("%(who)s added %(mode)sitive data '%(data)s' to nbc %(name)s"%{'who':nm_to_n(query.From()),'data':_match.group("data"),'name':_match.group("name"),'mode':mode})
			else:
				return self.Unhandled()
		else:
			return self.Unhandled()

class BayesTrigger(BotCommand):
	
	_classifiers = {}

	_cObj = {}

	_last = ""
	_lastClassifier = ""

	def Try(self,bot,query):

		if len(self._classifiers) == 0:
			self._getClassifiers(bot)
		results = {}
		for name in self._classifiers:
			if not name in self._cObj:
				self._cObj[name] = BayesClassifyer(bot,name)
			results[name] = self._cObj[name].getProbability(query.Message())
		
		best = 0.5 #we dont want anything below 0.5 being triggered
		trigger = []
		bestName = ""

		for name in results:
			if results[name] > self._classifiers[name]["threshold"]:
				if results[name] == best:
					trigger = trigger + self._classifiers[name]["triggers"]
					bestName += ', '+name
				elif results[name] > best:
					best = results[name]
					trigger = self._classifiers[name]["triggers"]
					bestName = name

		r = random.randint(0,cfg.config["nbcTriggerChance"])
		if len(trigger) > 0:
			self._last = query.Message()
			self._lastClassifier = bestName
			if r == 0:
				bot.getCommand('factoidtrigger').triggerFactoid(pickOne(trigger),bot,query)
				return self.Handled("Triggered nbc '%s' at probability %f"%(bestName,best))
			else:
				bot.log("Supressed triggering nbc '%s' at probability %f"%(bestName,best))
				return self.Unhandled()
		else:
			return self.Unhandled()

	def _getClassifiers(self, bot):
		data = bot.sql(r'select * from pail_nbcconfig;',(),["name","threshold","triggers"])
		newclassifier = {}
		for c in data:
			newclassifier[c["name"]] = {'threshold':c["threshold"],"triggers":c["triggers"].split(';')}
		self._classifiers = newclassifier
	
class BayesClassifyer():

	_bot = None
	_posCache = []
	_negCache = []
	_respCache = {}
	_probCache = []
	_name = ""

	def __init__(self, bot, name):
		self._bot = bot
		self._name = name

	def invalidateCache(self):
		self._posCache = []
		self._negCache = []
		self._respCache = {}
		self._probCache = []

	def getPosData(self):
		if len(self._posCache) == 0:
			self._posCache = self._bot.sql(r'select document from pail_nbcdata where nbcname=%s and mode=%s;',(self._name,"pos"),["document"])
		return self._posCache

	def getNegData(self):
		if len(self._negCache) == 0:
			self._negCache = self._bot.sql(r'select document from pail_nbcdata where nbcname=%s and mode=%s;',(self._name,"neg"),["document"])
		return self._negCache

	def getProbability(self, prompt):
		numWordsInNgram = 1
		prompt = self.cleanDocument(prompt)
		if prompt in self._respCache:
			return self._respCache[prompt]
		else:
			ngrams = self.getNgrams(prompt,numWordsInNgram)
			if len(self._probCache) > 0:
				probs = self._probCache[:]
			else:
				probs = self.getNgramBayesianProbabilities(numWordsInNgram)

			n = 0
			for ngram in ngrams:
				if ngram in probs and probs[ngram] > 0:
					n += math.log(1 - probs[ngram]) - math.log(probs[ngram])	
			prob = 1.0/(1.0+math.exp(n))
			self._respCache[prompt] = prob
			return prob
	
	
	def cleanDocument(self, document):
		pRegx = re.compile(r"\=|\@|\#|\||\+|\-|\,|\.|\!|\?|\"\'|\:|\;|\(|\)|\[|\]|\{|\}|\/|\\")
		tRegx = re.compile(r"^\s+|\s+$")
		wRegx = re.compile(r"\s{2,}")
		document = pRegx.sub("",document)
		document = document.lower()
		document = tRegx.sub("",document)
		document = wRegx.sub(" ",document)
		return document
		
	def getNgrams(self, document, numWordsInNgram):
		words = document.split()
		ngrams = []

		w = 0
		while w+numWordsInNgram <= len(words):
			ngram = ""
			n = 0
			while(n< numWordsInNgram):
				ngram += words[w+n]
				if(n+1 < numWordsInNgram):
					ngram += " "
				n+= 1
			ngrams.append(ngram)
			w+=1
		
		return ngrams
	
	def getNgramBayesianProbabilities(self, numWordsInNgram):
		probabilities = {}
		posNgramFrequencyData = self.getNgramFrequencies(self.getPosData(),numWordsInNgram)
		negNgramFrequencyData = self.getNgramFrequencies(self.getNegData(),numWordsInNgram)
		posNgramFrequencies = posNgramFrequencyData["ngramFrequencies"]
		negNgramFrequencies = negNgramFrequencyData["ngramFrequencies"]

		for ngram in posNgramFrequencies:
			if ngram in negNgramFrequencies:
				probabilities[ngram] = posNgramFrequencies[ngram] / (posNgramFrequencies[ngram]+ negNgramFrequencies[ngram])	

		return probabilities

	def getNgramFrequencies(self, documents, numWordsInNgram):
		ngramFrequencies = {}
		totalNgrams = 0
		countNgramOncePerDoc = False


		for d in range(0,len(documents) - 1):
			nDoc = self.cleanDocument(documents[d]["document"])

			ngrams = self.getNgrams(nDoc,numWordsInNgram)

			if not ngrams:
				continue
			
			if countNgramOncePerDoc:
				countedNgrams = []
			
			for n in range(0,len(ngrams)- 1):
				totalNgrams += 1
				if countNgramOncePerDoc:
					if countedNgrams[ngrams[n]]:
						continue
					else:
						countedNgrams[ngrams[n]] = true
				if ngrams[n] in ngramFrequencies:
					ngramFrequencies[ngrams[n]] += 1.0
				else:
					ngramFrequencies[ngrams[n]] = 1.0
		
		return {"ngramFrequencies": ngramFrequencies, "totalNgrams": totalNgrams}