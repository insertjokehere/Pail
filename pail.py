
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import re
import MySQLdb
import random

config = {
	'channels': ['#projectpail'],
	'server':'server1.entirelyrandom.net',
	'port':6667,
	'nickname':'pail',
	'disabledCommands':[],
	'admins':['Will'],
	'logChannel':'#projectpail',
	'dbHost':'127.0.0.1',
	'dbUser':'root',
	'dbPass':'not-my-real-password',
	'dbDB':'bucket',
	'ignore':[]
}

class BotCommand:
	def RequiresAdmin(self):
		return False
		
	def Try(self, bot, query):
		return {'handled':False}

	def OK(self,bot,query):
		c=bot.connection
		c.privmsg(query.RespondTo(),"Ok, %(who)s" % {'who':nm_to_n(query.From())})

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
			cursor.execute('select triggerkey,method,response,id from bucket_facts where triggerkey="%(trigger)s";' % {'trigger':query.Message()})
			facts = cursor.fetchall()
			cursor.close()
		if len(facts) > 0:
			self._cache[query.Message()] = facts
			fact = facts[random.randint(0,len(facts)-1)]
			self.lastID = fact[3]
			if fact[1]== 'reply':
				c.privmsg(query.RespondTo(),fact[2])
			elif fact[1] == 'action':
				c.action(query.RespondTo(),fact[2])
			else:
				c.privmsg(query.RespondTo(),"%(key)s %(method)s %(response)s"%{'key':fact[0],'method':fact[1],'response':fact[2]})
			resp = {'handled':True,'debug':"#%(num)u: %(key)s => <%(method)s> %(response)s (Cached: %(isCached)s)"%{'key':fact[0],'method':fact[1],'response':fact[2],'num':fact[3],'isCached':isCached}}
			bot.log(resp['debug'])
			return resp
		else:
			return {'handled':False}
	
	def ClearCache(self, key=""):
		if key=="":
			self._cache = {}
		elif key in self._cache:
			del self._cache[key]

class TeachFactoid(BotCommand):
	
	def __init__(self):
		self._rx = re.compile(r'([\s.,!#&*:;\'\"\w]+) <(\w+)> ([\s.,!#&*:;\'\"\w@$%]+)',re.IGNORECASE)
		
	def Try(self,bot,query):
		c=bot.connection
		_match = self._rx.match(query.Message())
		if _match and query.Directed():
			if _match.group(1).strip() != "" and _match.group(2).strip() != "" and _match.group(2).strip() != "":
				cursor = bot.db()
				cursor.execute(r"insert into bucket_facts values('%(key)s','%(method)s','%(resp)s',0,0);"%{'key':_match.group(1).strip(),'method':_match.group(2).strip(),'resp':_match.group(3).strip()})
				cursor.close()
				bot.getCommand('factoidtrigger').ClearCache(_match.group(1).strip())
				self.OK(bot,query)
				resp = {'handled':True,'debug':"%(who)s added %(key)s => <%(method)s> %(response)s"%{'key':_match.group(1).strip(),'method':_match.group(2).strip(),'response':_match.group(3).strip(),'who':query.From()}}
				bot.log(resp['debug'])
				return resp
		return {'handled':False}
			
class CommandModeChange(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(disable|enable) command:? (\w+)',re.IGNORECASE)

	def Try(self, bot, query):
		c=bot.connection
		_match = self._rx.match(query.Message())
		if _match and query.Directed():
			if _match.group(1).lower() == 'disable':
				bot.disableCommand(_match.group(2))
				self.OK(bot,query)
				bot.log("%(who)s disabled command %(command)s"%{'who':query.From(),'command':_match.group(2)})
				return {'handled':True,'debug':'commandmodechange: enable/disable a command'}
			elif _match.group(1).lower() == 'enable':
				bot.enableCommand(_match.group(2))
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
		self._rx = re.compile(r'(join|part) (#[\w-]+)',re.IGNORECASE)

	def RequiresAdmin(self):
		return True
		
	def Try(self,bot,query):
		c=bot.connection
		_match = self._rx.match(query.Message())
		if query.Directed() and _match:
			if _match.group(1) == "join":
				bot.connection.join(_match.group(2))
			else:
				bot.connection.part(_match.group(2))
			self.OK(bot,query)
			resp={'handled':True,'debug':'%(mode)sed %(chan)s at the request of %(who)s'%{'mode':_match.group(1),'chan':_match.group(2),'who':query.From()}}
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

class IrcQuery:
	def __init__(self,fromuser,respondto,messagetext,directed=False):
		self._from = fromuser
		self._respondto = respondto
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
			'joinpartcommand':JoinPartCommand()
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
		q = IrcQuery(e.source(),e.target(),e.arguments()[0])
		self.processQuery(q)

	def on_dccmsg(self, c, e):
		c.privmsg("You said: " + e.arguments()[0])

	def on_dccchat(self, c, e):
		if len(e.arguments()) != 2:
			return
		args = e.arguments()[1].split()
		if len(args) == 4:
			try:
				address = ip_numstr_to_quad(args[2])
				port = int(args[3])
			except ValueError:
				return
			self.dcc_connect(address, port)
		
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
	
def main():	
	bot = Pail(config['nickname'], config['server'], config['port'])
	bot.start()

if __name__ == "__main__":
	main()