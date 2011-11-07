from common import *
import re
import random

def Factory():
	return {
		'deletevariable':DeleteVariable(),
		'protectvariable':ProtectVariable(),
		'addvar':AddVar(),
		'lookupvar':LookupVar()
	}

class DeleteVariable(DeleteCommand):
	def __init__(self):
		DeleteCommand.__init__(self,r"(forget|delete)\s+var(iable)?\s+(?P<id>(#\d+)|(\w+))",'variable','bucket_vars',self._clearCache)
	
	def _clearCache(self,bot,key):
		bot.getCommand('lookupvar').clearCache(key)
		
class ProtectVariable(ProtectCommand):
	def __init__(self):
		ProtectCommand.__init__(self,'variable',r'(?P<mode>protect|unprotect) var(iable)? (?P<key>(#\d+)|(\w+))','bucket_vars')

class AddVar(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(?P<name>\w+)\s*:=\s*(?P<value>.+)',re.IGNORECASE)
	
	def Try(self,bot,query):
		if query.Directed():
			_match=self._rx.match(query.Message())
			if _match:			
				name=_match.group('name')
				value = _match.group('value')
				cursor=bot.db()
				cursor.execute('insert into bucket_vars (name,value,protected) values(%s,%s,%s)',(name,value,0))
				cursor.close()
				self.OK(bot,query)
				resp = {'handled':True,'debug':"%(who)s added value '%(val)s' to variable %(name)s"%{'who':nm_to_n(query.From()),'val':value,'name':name}}
				bot.log(resp['debug'])
				return resp
		return {'handled':False}
		
class LookupVar(BotCommand):
	
	def __init__(self):
		self._cache={}
		self._internalVars={
			'admin':self._admin,
			'who':self._who,
			'someone':self._someone,
			'op':self._admin
		}
		self._rx_find = re.compile(r'\$(\w+)',re.IGNORECASE)
		self._rx = re.compile(r'(what is|show) var(iable)? \$?(?P<varname>\w+)\??',re.IGNORECASE)
	
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				varname = _match.group('varname')
				self.replaceVars(bot,query,'$'+varname) #if the variable exists, it will be in the cache (unless it is a built-in)
				if varname in self._cache:
					msg = "%(varname)s: ["%{'varname':varname}
					for v in self._cache[varname]:
						msg += "%(id)s:'%(value)s', "%{'value':v['value'],'id':v['id']}
					msg = msg[:-2]+"]"
					bot.connection.privmsg(query.RespondTo(),msg)
					resp = {'handled':True,'debug':"%(who)s looked up variable '%(varname)s'"%{'who':nm_to_n(query.From()),'varname':varname}}
					bot.log(resp['debug'])
					return resp
				else:
					bot.command.privmsg(query.RespondTo(),"I don't know about that variable, %(who)s"%{'who':nm_to_n(query.From())})
					resp = {'handled':True,'debug':"%(who)s looked up unknown variable '%(varname)s'"%{'who':nm_to_n(query.From()),'varname':varname}}
				bot.log(resp['debug'])
				return resp
		return {'handled':False}
	
	def clearCache(self,name):
		if name in self._cache:
			del self._cache[name]
			
	def _admin(self,bot,query):
		return config('admins')[random.randint(0,len(config('admins'))-1)]
	
	def _who(self,bot,query):
		print 'who'
		return nm_to_n(query.From())
	
	def _someone(self,bot,query):
		users = bot.channels[query.Channel()].users()
		for u in config('ignore'):
			if u in users:
				users.remove(u)
		if config('nickname') in users:
			users.remove(config('nickname'))
		return users[random.randint(0,len(users)-1)]
	
	def replaceVars(self,bot,query,message):
		return self._rx_find.sub(self._replacer(bot,query,self)._replace,message)
		
	class _replacer:
		
		def __init__(self,bot,query,parent):
			self._bot = bot
			self._query = query
			self._parent = parent
	
		def _replace(self,_match):
			varname = _match.group(1)
			if varname in self._parent._internalVars:
				return self._parent._internalVars[varname](self._bot,self._query)
			elif varname in self._parent._cache:
				return self._parent._cache[varname][random.randint(0,len(self._parent._cache[varname])-1)]['value']
			else:
				cursor = self._bot.db()
				cursor.execute(r"select value,id from bucket_vars where name=%s",(varname.lower()))
				vars = tuppleToList(['value','id'],cursor.fetchall())
				if len(vars)>0:
					self._parent._cache[varname]=vars
					return self._parent._cache[varname][random.randint(0,len(self._parent._cache[varname])-1)]['value']
				else:
					return varname
