"""
Pail IRC Bot
(c) William Hughes, 2011
Licence is yet to be determined

Requires:
irclib <http://python-irclib.sourceforge.net/>
MySQLdb <http://mysql-python.sourceforge.net/>
"""

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import re
import MySQLdb
import random
import json
import sys 

config = {}

class BotCommand:
	def RequiresAdmin(self):
		return False
		
	def Try(self, bot, query):
		return {'handled':False}

	def OK(self,bot,query):
		c=bot.connection
		c.privmsg(query.RespondTo(),"Ok, %(who)s" % {'who':nm_to_n(query.From())})
		
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
		return config['admins'][random.randint(0,len(config['admins'])-1)]
	
	def _who(self,bot,query):
		print 'who'
		return nm_to_n(query.From())
	
	def _someone(self,bot,query):
		users = bot.channels[query.Channel()].users()
		for u in config['ignore']:
			if u in users:
				users.remove(u)
		if config['nickname'] in users:
			users.remove(config['nickname'])
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
				

class DeleteCommand(BotCommand):
	def __init__(self, regex, type, table,clearcachefunction):
		self._rx=re.compile(regex,re.IGNORECASE)
		self._type=type
		self._table=table
		self._clearCache = clearcachefunction
	
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				cursor = bot.db()
				if _match.group('id')[0] == "#": #delete by id number, otherwise by key
					id=_match.group('id')[1:]
					cursor.execute('select name,protected from %(table)s where id=%%s'%{'table':self._table},(id))
					entry = tuppleToList(['key','protected'],cursor.fetchall())[0] #id is the primary key, so there will only be one tupple returned
					if (entry['protected']==1 and isAdmin(query.From())) or entry['protected'] == 0:
						self._clearCache(bot,entry['key'])
						cursor.execute('delete from %(table)s where id=%%s'%{'table':self._table},(id))
						cursor.close()
						self.OK(bot,query)
						resp = {'handled':True,'debug':'deleted %(type)s #%(num)s for %(who)s'%{'type':self._type,'num':id,'who':nm_to_n(query.From())}}
					else:
						bot.connection.privmsg(query.RespondTo(),"Sorry %(who)s, that %(type)s is protected"%{'who':nm_to_n(query.From()),'type':self._type})
						resp = {'handled':True,'debug':'%(who)s attempted to delete protected %(type)s #%(num)s'%{'who':query.From(),'num':id,'type':self._type}}
				elif isAdmin(query.From()): #batch delete, requires admin
					key=_match.group('id')
					cursor.execute('delete from %(table)s where name=%%s'%{'table':self._table},(key))
					cursor.close()
					self.OK(bot,query)
					resp={'handled':True,'debug':"deleted %(type)s '%(key)s' for %(who)s"%{'type':self._type,'who':query.From(),'key':key}}
				else:
					bot.connection.privmsg(query.RespondTo(),"Sorry %(who)s, you need to be an admin to do that"%{'who':nm_to_n(query.From())})
					resp = {'handled':True,'debug':"%(who)s attempted to batch delete factoid '%(key)s'"%{'who':query.From(),'key':key}}
				bot.log(resp['debug'])
				return resp
		return {'handled':False}

class DeleteFactoid(DeleteCommand):
	def __init__(self):
		DeleteCommand.__init__(self,r"(forget|delete)\s+fact(oid)?\s+(?P<id>#(\d+)|([^@$%]+))",'factoid','bucket_facts',self._clearCache)
		
	def _clearCache(self,bot,key):
		bot.getCommand('factoidtrigger').clearCache(key)
		
class DeleteVariable(DeleteCommand):
	def __init__(self):
		DeleteCommand.__init__(self,r"(forget|delete)\s+var(iable)?\s+(?P<id>#(\d+)|(\w+))",'variable','bucket_vars',self._clearCache)
	
	def _clearCache(self,bot,key):
		bot.getCommand('lookupvar').clearCache(key)
		
class ProtectFactoid(BotCommand):
#todo: batch protect/unprotect by key, modify to work with vars as well similar to delete
	def __init__(self):
		self._rx = re.compile(r'(protect|unprotect) (factoid )?#(\d+)',re.IGNORECASE)
		
	def RequireAdmin(self):
		return True
	
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				cursor = bot.db()
				if _match.group(1).lower() == "unprotect":
					mode = 0
				else:
					mode = 1
				cursor.execute(r'update bucket_facts set protected=%s where id=%s',(mode,_match.group(3)))
				cursor.close()
				self.OK(bot,query)
				resp = {'handled':True,'debug':'%(mode)sed factoid #%(num)s for %(who)s'%{'mode':_match.group(1),'num':_match.group(3),'who':query.From()}}
				bot.log(resp['debug'])
				return resp
		return {'handled':False}
		
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
			print query.Message()
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
			
class CommandModeChange(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(?P<method>disable|enable) command:? (?P<command>\w+)',re.IGNORECASE)

	def Try(self, bot, query):
		c=bot.connection
		_match = self._rx.match(query.Message())
		if _match and query.Directed():
			if _match.group('method').lower() == 'disable':
				bot.disableCommand(_match.group('command'))
				self.OK(bot,query)
				bot.log("%(who)s disabled command %(command)s"%{'who':query.From(),'command':_match.group(2)})
				return {'handled':True,'debug':'commandmodechange: enable/disable a command'}
			elif _match.group('method').lower() == 'enable':
				bot.enableCommand(_match.group('command'))
				self.OK(bot,query)
				bot.log("%(who)s enabled command %(command)s"%{'who':query.From(),'command':_match.group(2)})
				return {'handled':True,'debug':'commandmodechange: enable/disable a command'}
			else:
				return {'handled':False}
		else:
			return {'handled':False}
			
	def RequireAdmin(self):
		return True

class JoinPartCommand(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(?P<mode>join|part) (?P<channel>#[\w-]+)',re.IGNORECASE)

	def RequiresAdmin(self):
		return True
		
	def Try(self,bot,query):
		c=bot.connection
		_match = self._rx.match(query.Message())
		if query.Directed() and _match:
			if _match.group('mode') == "join":
				bot.connection.join(_match.group('channel'))
			else:
				bot.connection.part(_match.group('channel'))
			self.OK(bot,query)
			resp={'handled':True,'debug':'%(mode)sed %(chan)s at the request of %(who)s'%{'mode':_match.group('mode'),'chan':_match.group('channel'),'who':query.From()}}
			bot.log(resp['debug'])
			return resp
		return {'handled':False}
		
class TestCommand(BotCommand):
	def Try(self, bot, query):
		c = bot.connection
		if query.Directed() and query.Message().lower() == 'test':
			c.privmsg(query.RespondTo(),query.Message())
			return {'handled':True,'debug':'test: test command'}
		else:
			return {'handled':False}

class AdminTest(BotCommand):
	def __init__(self):
		self._rx = re.compile('am i an admin\??',re.IGNORECASE)
		
	def Try(self,bot,query):
		c = bot.connection
		_match = self._rx.match(query.Message())
		if query.Directed() and _match:
			c.privmsg(query.RespondTo(),"You are an admin, %(who)s"%{'who':query.From()})
			return {'handled':True,'debug':'admintest: admin test command'}
		else:
			return {'handled':False}
		
	def RequiresAdmin(self):
		return True

def isAdmin(username):
	return nm_to_n(username) in config['admins']

def tuppleToList(names,tupple):
	list = []
	for t in tupple:
		m = {}
		i=0
		for n in names:
			m[n]=t[i]
			i += 1
		list.append(m)
	return list
	
class IrcQuery:
	def __init__(self,fromuser,respondto,messagetext,channel="",directed=False):
		self._from = fromuser
		self._respondto = respondto
		self._channel = channel
		if messagetext.lower().startswith(config['nickname']+": "):
			self._messagetext = messagetext[len(config['nickname'])+2:].strip()
			self._directed = True
		else:
			self._messagetext = messagetext.strip()
			self._directed = directed
	
	def Message(self):
		return self._messagetext
	
	def From(self):
		return self._from
	
	def RespondTo(self):
		return self._respondto
	
	def Directed(self):
		return self._directed
		
	def Channel(self):
		return self._channel

class Pail(SingleServerIRCBot):
	def __init__(self, nickname, server, port=6667):
		SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		#self.channel = channel
		self._db = False
		self._connectDB()

		self.commands = {
			'test':TestCommand(),
			'admintest':AdminTest(),
			'commandmodechange':CommandModeChange(),
			'factoidtrigger':FactoidTrigger(),
			'teachfactoid':TeachFactoid(),
			'joinpartcommand':JoinPartCommand(),
			'deletefactoid':DeleteFactoid(),
			'protectfactoid':ProtectFactoid(),
			'lookupvar':LookupVar(),
			'deletevariable':DeleteVariable(),
			'addvar':AddVar()
		}

		self.disabledCommands = {}
		
		for c in config['disabledCommands']:
			self.disableCommand(c)

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")

	def on_welcome(self, c, e):
		for ch in config['channels']:
			self.connection.join(ch)

	def on_privmsg(self, c, e):
		q = IrcQuery(e.source(),e.source(),e.arguments()[0],True)
		self.processQuery(q)

	def on_pubmsg(self, c, e):
		q = IrcQuery(e.source(),e.target(),e.arguments()[0],channel=e.target())
		self.processQuery(q)
		
	def log(self, logtext):
		c = self.connection
		print logtext
		if config['logChannel']:
			c.privmsg(config['logChannel'],logtext)
		
	def processQuery(self, query):
		if not nm_to_n(query.From()) in config['ignore']:
			for cmd in self.commands.values():
				if (cmd.RequiresAdmin() and isAdmin(query.From())) or not cmd.RequiresAdmin():
					result = cmd.Try(self,query)
					if result['handled']:
						self._lastDebug = result['debug']
						self._db.commit()
						break
	
	def disableCommand(self, command):
		self.disabledCommands[command] = self.commands[command]
		del self.commands[command]
			
	def enableCommand(self,command):
		self.commands[command]=self.disabledCommands[command]
		del self.disabledCommands[command]
	
	def getCommand(self, command):
		if command in self.commands:
			return self.commands[command]
		else:
			return self.disabledCommands[command]
	
	def _connectDB(self):
		self._db = MySQLdb.connect(host=config['dbHost'],user=config['dbUser'],passwd=config['dbPass'],db=config['dbDB'])
	
	def db(self):
		if not self._db:
			self._connectDB()
		return self._db.cursor()
	
	def saveConfig(self):
		stream = open('pail.yml','w')
		json.dump(config,stream, sort_keys=True, indent=4)
		stream.close()
	
def main():	
	global configfile, config
	if len(sys.argv) > 1:
		configfile = sys.argv[1]
	else:
		configfile = 'pail.json'
	f = open(configfile,'r')
	config = json.load(f)
	f.close()
	bot = Pail(config['nickname'], config['server'], config['port'])
	bot.start()

configfile = ""	

if __name__ == "__main__":
	main()
