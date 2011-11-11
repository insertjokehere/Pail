from common import *
import re
import random
import cfg

class Factory(CommandModuleFactory):
	def Commands(self):
		return {
			'deletefactoid':DeleteFactoid(),
			'protectfactoid':ProtectFactoid(),
			'factoidtrigger':FactoidTrigger(),
			'teachfactoid':TeachFactoid()
		}
		
class DeleteFactoid(DeleteCommand):
	def __init__(self):
		DeleteCommand.__init__(self,r"(forget|delete)\s+fact(oid)?\s+(?P<id>(#\d+)|([^@$%]+))",'factoid','pail_facts',self._clearCache)
		
	def _clearCache(self,bot,key):
		bot.getCommand('factoidtrigger').clearCache(key)
		
class ProtectFactoid(ProtectCommand):
	def __init__(self):
		ProtectCommand.__init__(self,'factoid',r'(?P<mode>protect|unprotect) fact(oid)? (?P<key>(#\d+)|([^@$%]+))','pail_facts')
		
class FactoidTrigger(BotCommand):
	
	def __init__(self):
		self._cache = {}
	
	def Try(self,bot,query):
		if query.Message() in bot.getExport('specialfactoids'):
			return self.Unhandled()
		r = self._getFactoid(query.Message(),bot)
		isCached = r['isCached']
		facts = r['facts']
		
		if len(facts) > 0:
			fact = self.sayFactoid(facts,bot,query)
			resp = self.Handled("#%(num)u: %(key)s => <%(method)s> %(response)s (Cached: %(isCached)s)"%{'key':fact['key'],'method':fact['method'],'response':fact['response'],'num':fact['id'],'isCached':isCached})
			bot.log(resp['debug'])
			return resp
		else:
			return self.Unhandled()
	
	def triggerFactoid(self,name,bot,query,this=None):
		self.sayFactoid(self._getFactoid(name,bot)['facts'],bot,query,this)
	
	def _getFactoid(self,name,bot):
		isCached = False
		if name in self._cache:
			facts = self._cache[name]
			isCached = True
		else:
			facts = bot.sql(r'select name,method,response,id from pail_facts where name=%s;',(name),['key','method','response','id'])
			if len(facts) > 0:
				self._cache[name] = facts
				
		return {'isCached':isCached,'facts':facts}
	
	def clearCache(self, key=""):
		if key=="":
			self._cache = {}
		elif key in self._cache:
			del self._cache[key]
			
	def sayFactoid(self, facts, bot, query,this=None):
		if type(facts) is dict:
			fact = facts
		else:
			fact = pickOne(facts)
		message = fact['response']
		if fact['method']== 'reply':
			bot.say(query,message,this=this)
		elif fact['method'] == 'action':
			bot.say(query,message,this=this,mode='action')
		elif fact['method'] == 'alias':
			bot.log("Following alias for %(fact)s"%{"fact":fact['key']})
			f = self._getFactoid(fact['response'],bot)['facts']
			return self.sayFactoid(f,bot,query,this)
		else:
			bot.say(query,"%(key)s %(method)s %(response)s"%{'key':fact['key'],'method':fact['method'],'response':message},this=this)
		return fact

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
				if key in bot.getExport('specialfactoids') and not isAdmin(query.From()):
					resp = self.Handed("Sorry %(who)s, you need to be an admin to modify that"%{'who':nm_to_n(query.From())})
				else:
					bot.sql(r"insert into pail_facts (name,method,response,id,protected) values(%s,%s,%s,0,0);",(key,method,response))
					bot.getCommand('factoidtrigger').clearCache(_match.group(1).strip())
					self.OK(bot,query)
					resp = self.Handled("%(who)s added %(key)s => <%(method)s> %(response)s"%{'key':key,'method':method,'response':response,'who':query.From()})
				bot.log(resp['debug'])
				return resp
		return self.Unhandled()
		
