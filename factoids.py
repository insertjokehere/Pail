from common import *
import re
import random

def Factory():
	return {
		'deletefactoid':DeleteFactoid(),
		'protectfactoid':ProtectFactoid(),
		'factoidtrigger':FactoidTrigger(),
		'teachfactoid':TeachFactoid()
	}

class DeleteFactoid(DeleteCommand):
	def __init__(self):
		DeleteCommand.__init__(self,r"(forget|delete)\s+fact(oid)?\s+(?P<id>(#\d+)|([^@$%]+))",'factoid','bucket_facts',self._clearCache)
		
	def _clearCache(self,bot,key):
		bot.getCommand('factoidtrigger').clearCache(key)
		
class ProtectFactoid(ProtectCommand):
	def __init__(self):
		ProtectCommand.__init__(self,'factoid',r'(?P<mode>protect|unprotect) fact(oid)? (?P<key>(#\d+)|([^@$%]+))','bucket_facts')
		
class FactoidTrigger(BotCommand):
	
	def __init__(self):
		self._cache = {}
	
	def Try(self,bot,query):
		c=bot.connection
		isCached = False
		if query.Message() in self._cache:
			facts = self._cache[query.Message()]
			isCached = True
		else:
			cursor = bot.db()
			cursor.execute('select name,method,response,id from bucket_facts where name=%s;',(query.Message()))
			facts = tuppleToList(['key','method','response','id'],cursor.fetchall())
			cursor.close()
		if len(facts) > 0:
			self._cache[query.Message()] = facts
			fact = facts[random.randint(0,len(facts)-1)]
			self.lastID = fact['id']
			message = bot.getCommand('lookupvar').replaceVars(bot,query,fact['response'])
			if fact['method']== 'reply':
				c.privmsg(query.RespondTo(),message)
			elif fact['method'] == 'action':
				c.action(query.RespondTo(),message)
			else:
				c.privmsg(query.RespondTo(),"%(key)s %(method)s %(response)s"%{'key':fact['key'],'method':fact['method'],'response':message})
			resp = {'handled':True,'debug':"#%(num)u: %(key)s => <%(method)s> %(response)s (Cached: %(isCached)s)"%{'key':fact['key'],'method':fact['method'],'response':fact['response'],'num':fact['id'],'isCached':isCached}}
			bot.log(resp['debug'])
			return resp
		else:
			return {'handled':False}
	
	def clearCache(self, key=""):
		if key=="":
			self._cache = {}
		elif key in self._cache:
			del self._cache[key]

class TeachFactoid(BotCommand):
	
	def __init__(self):
		self._rx = re.compile(r'(?P<key>[^@$%]+) <(?P<method>\w+)> (?P<response>.+)',re.IGNORECASE)
		
	def Try(self,bot,query):
		c=bot.connection
		_match = self._rx.match(query.Message())
		if _match and query.Directed():
			if _match.group('key').strip() != "" and _match.group('method').strip() != "" and _match.group('response').strip() != "":
				key = _match.group('key').strip()
				method = _match.group('method').strip()
				response = _match.group('response').strip()
				cursor = bot.db()
				cursor.execute(r"insert into bucket_facts (name,method,response,id,protected) values(%s,%s,%s,0,0);",(key,method,response))
				cursor.close()
				bot.getCommand('factoidtrigger').clearCache(_match.group(1).strip())
				self.OK(bot,query)
				resp = {'handled':True,'debug':"%(who)s added %(key)s => <%(method)s> %(response)s"%{'key':key,'method':method,'response':response,'who':query.From()}}
				bot.log(resp['debug'])
				return resp
		return {'handled':False}
		