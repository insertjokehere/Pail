"""
Pail IRC Bot
(c) William Hughes, 2011
Licence is yet to be determined

Requires:
irclib <http://python-irclib.sourceforge.net/>
MySQLdb <http://mysql-python.sourceforge.net/>
"""

from ircbot import SingleServerIRCBot, IRCDict
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import re
import MySQLdb
import random
import sys 
from common import *
import factoids
import variables
import inventory
import cfg
import randomness

class LastDebugCommand(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(what was that\??|debug last|what\??)$',re.IGNORECASE)
		
	def Try(self,bot,query):
		if query.Directed() and 'message' in bot._lastDebug:
			_match = self._rx.match(query.Message())
			if _match:
				bot.say(query,"That was: (%(lastsource)s) '%(lastmessage)s'"%{'lastmessage':bot._lastDebug['message'],'lastsource':bot._lastDebug['source']})
				return self.Handled()
		return self.Unhandled()
		
class CommandModeChange(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(?P<method>disable|enable) command:? (?P<command>\w+)',re.IGNORECASE)

	def Try(self, bot, query):
		c=bot.connection
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				if _match.group('method').lower() == 'disable':
					bot.disableCommand(_match.group('command'))
					self.OK(bot,query)
					bot.log("%(who)s disabled command %(command)s"%{'who':query.From(),'command':_match.group(2)})
					return self.Handled('commandmodechange: enable/disable a command')
				elif _match.group('method').lower() == 'enable':
					bot.enableCommand(_match.group('command'))
					self.OK(bot,query)
					bot.log("%(who)s enabled command %(command)s"%{'who':query.From(),'command':_match.group(2)})
					return self.Handled('commandmodechange: enable/disable a command')
				else:
					return self.Unhandled()
		return self.Unhandled()
			
	def RequireAdmin(self):
		return True

class JoinPartCommand(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(?P<mode>join|part) (?P<channel>#[\w-]+)',re.IGNORECASE)

	def RequiresAdmin(self):
		return True
		
	def Try(self,bot,query):
		c=bot.connection
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				if _match.group('mode') == "join":
					bot.connection.join(_match.group('channel'))
				else:
					bot.connection.part(_match.group('channel'))
				self.OK(bot,query)
				resp=self.Handled('%(mode)sed %(chan)s at the request of %(who)s'%{'mode':_match.group('mode'),'chan':_match.group('channel'),'who':query.From()})
				bot.log(resp['debug'])
				return resp
		return self.Unhandled()
		
class TestCommand(BotCommand):
	def Try(self, bot, query):
		if query.Directed() and query.Message().lower() == 'test':
			bot.say(query,query.Message())
			return self.Handled('test: test command')
		else:
			return self.Unhandled()

class AdminTest(BotCommand):
	def __init__(self):
		self._rx = re.compile('am i an admin\??',re.IGNORECASE)
		
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				bot.say(query,"You are an admin, %(who)s"%{'who':nm_to_n(query.From())})
				return self.Handled('admintest: admin test command')
		return self.Unhandled()
		
	def RequiresAdmin(self):
		return True


	
class IrcQuery:
	def __init__(self,fromuser,respondto,messagetext,channel="",directed=False,isAction=False):
		self._from = fromuser
		self._respondto = respondto
		self._channel = channel
		self._IsAction = isAction
		if messagetext.lower().startswith(cfg.config['nickname'].lower()+": ") or messagetext.lower().startswith(cfg.config['nickname'].lower()+", "):
			self._messagetext = messagetext[len(cfg.config['nickname'])+2:].strip()
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
	
	def IsAction(self):
		return self._IsAction

class Pail(SingleServerIRCBot):
	def __init__(self, nickname, server, port=6667):
		SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		#self.channel = channel
		self._db = None
		
		modules = [factoids,variables,inventory,randomness]
		
		self._lastDebug = {}
		
		self.commands = {
			'test':TestCommand(),
			'admintest':AdminTest(),
			'commandmodechange':CommandModeChange(),
			'joinpartcommand':JoinPartCommand(),
			'lastdebucCommand':LastDebugCommand()
		}
		
		self.exports = {'specialfactoids':['dontknow']}
		
		self._defaults = {
				"server":"localhost",
				"port":6667,
				"nickname":"pail",
				"disabledCommands":[],
				"admins":[],
				"logChannel":"#pail-log",
				"dbHost":"127.0.0.1",
				"dbUser":"root",
				"dbPass":"not-my-real-password",
				"dbDB":"pail",
				"ignore":[],
				"channels":["#pail","#pail-log"]
			}
		
		for i in self._defaults.items():
			cfg.config.setDefault(i[0],i[1])
		
		for m in modules:
			f = m.Factory(self)
			for i in f.Defaults().items():
				cfg.config.setDefault(i[0],i[1])
			self.commands = dict(self.commands.items() + f.Commands().items())
			exp = f.Exports()
			for k in exp:
				if k in self.exports:
					self.exports[k].extend(exp[k])
				else:
					self.exports[k] = exp[k]
			for i in f.TimerFunctions():
				if not 'arguments' in i.keys():
					args = ()
				else:
					args = i['arguments']
				self.execute_every(i['interval'],i['function'],args)
		
		self.disabledCommands = {}
		
		for c in cfg.config['disabledCommands']:
			self.disableCommand(c)

	def on_action(self, c,e):
		q=IrcQuery(e.source(),e.target(),e.arguments()[0],isAction=True)
		self.processQuery(q)
		
	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")

	def on_welcome(self, c, e):
		for ch in cfg.config['channels']:
			self.connection.join(ch)

	def on_privmsg(self, c, e):
		q = IrcQuery(e.source(),e.source(),e.arguments()[0],directed=True)
		self.processQuery(q)

	def on_pubmsg(self, c, e):
		q = IrcQuery(e.source(),e.target(),e.arguments()[0],channel=e.target())
		self.processQuery(q)
	
	def on_nick(self, c, e):
		if nm_to_n(e.source()) == cfg.config['nickname']:
			cfg.config['nickname'] = e.target()
		
	def log(self, logtext):
		c = self.connection
		print logtext
		if cfg.config['logChannel']:
			c.privmsg(cfg.config['logChannel'],logtext)
		
	def processQuery(self, query):
		if not nm_to_n(query.From()) in cfg.config['ignore']:
			handled = False
			for cmds in self.commands:
				cmd = self.commands[cmds]
				adminCheck = (cmd.RequiresAdmin() and isAdmin(query.From())) or not cmd.RequiresAdmin() #true if the admin requirements are met
				actionCheck = not(cmd.IgnoreActions() and query.IsAction()) #check if the action requirements are met
				if adminCheck and actionCheck:
					result = cmd.Try(self,query)
					if result['handled']:
						if 'debug' in result:
							self._lastDebug = {'message':result['debug'],'source':cmds}
						if not self._db is None:
							self._db.commit()
						handled = True
						break
			if not handled and query.Directed():
				self.getCommand('factoidtrigger').triggerFactoid('dontknow',self,query)
	
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
	
	def getExport(self, name):
		if name in self.exports:
			return self.exports[name]
		else:
			return []
	
	def _connectDB(self):
		self._db = MySQLdb.connect(host=cfg.config['dbHost'],user=cfg.config['dbUser'],passwd=cfg.config['dbPass'],db=cfg.config['dbDB'])
	
	
	def sql(self, query, args, mapnames=None):
		if self._db is None:
			self._connectDB()
		try:
			cursor = self._db.cursor()
			cursor.execute(query,args)
			results = cursor.fetchall()
			cursor.close()
			if not mapnames is None:
				results = tuppleToList(mapnames,results)
			return results
		except (AttributeError, MySQLdb.OperationalError):
			self._connectDB()
			cursor = self._db.cursor()
			cursor.execute(query,args)
			results = cursor.fetchall()
			cursor.close()
			if not mapnames is None:
				results = tuppleToList(mapnames,results)
			return results
	def execute_every(self,interval,function,arguments):
		self.connection.execute_delayed(interval,self._execute_every,(interval,function,arguments))
		
	def _execute_every(self,interval,function,arguments):
		if not function(arguments):
			self.execute_every(interval,function,arguments)
	
	def say(self, query, message, this=None,mode="privmsg"):
		if 'lookupvar' in self.commands:
			message = self.getCommand('lookupvar').replaceVars(self,query,message,this)
		for filter in self.getExport('outputfilter'):
			message = filter(query, message, this)
		if mode=="privmsg":
			self.connection.privmsg(query.RespondTo(),message)
		elif mode=="action":
			self.connection.action(query.RespondTo(),message)
		
	
def main():	
	if len(sys.argv) > 1:
		configfile = sys.argv[1]
	else:
		configfile = 'pail.json'
	cfg.config = cfg.Config(configfile)
	bot = Pail(cfg.config['nickname'], cfg.config['server'], cfg.config['port'])
	bot.start()

if __name__ == "__main__":
	main()
