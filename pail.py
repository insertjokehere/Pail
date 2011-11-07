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
from common import *
import factoids
import variables

class LastDebugCommand(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(what was that\??|debug last|what\??)',re.IGNORECASE)
		
	def Try(self,bot,query):
		if query.Directed() and 'message' in bot._lastDebug:
			_match = self._rx.match(query.Message())
			if _match:
				bot.connection.privmsg(query.RespondTo(),"That was: (%(lastsource)s) '%(lastmessage)s'"%{'lastmessage':bot._lastDebug['message'],'lastsource':bot._lastDebug['source']})
				return {'handled':True}
		return {'handled':False}
		
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
					return {'handled':True,'debug':'commandmodechange: enable/disable a command'}
				elif _match.group('method').lower() == 'enable':
					bot.enableCommand(_match.group('command'))
					self.OK(bot,query)
					bot.log("%(who)s enabled command %(command)s"%{'who':query.From(),'command':_match.group(2)})
					return {'handled':True,'debug':'commandmodechange: enable/disable a command'}
				else:
					return {'handled':False}
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
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
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
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				c.privmsg(query.RespondTo(),"You are an admin, %(who)s"%{'who':query.From()})
				return {'handled':True,'debug':'admintest: admin test command'}
		return {'handled':False}
		
	def RequiresAdmin(self):
		return True


	
class IrcQuery:
	def __init__(self,fromuser,respondto,messagetext,channel="",directed=False):
		self._from = fromuser
		self._respondto = respondto
		self._channel = channel
		if messagetext.lower().startswith(config('nickname')+": "):
			self._messagetext = messagetext[len(config('nickname'))+2:].strip()
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
		
		self._lastDebug = {}

		self.commands = {
			'test':TestCommand(),
			'admintest':AdminTest(),
			'commandmodechange':CommandModeChange(),
			'joinpartcommand':JoinPartCommand(),
			'lastdebucCommand':LastDebugCommand()
		}
		
		modules = [factoids,variables]
		
		for m in modules:
			self.commands = dict(self.commands.items() + m.Factory().items())
		
		self.disabledCommands = {}
		
		for c in config('disabledCommands'):
			self.disableCommand(c)

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")

	def on_welcome(self, c, e):
		for ch in config('channels'):
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
		if config('logChannel'):
			c.privmsg(config('logChannel'),logtext)
		
	def processQuery(self, query):
		if not nm_to_n(query.From()) in config('ignore'):
			for cmds in self.commands:
				cmd = self.commands[cmds]
				if (cmd.RequiresAdmin() and isAdmin(query.From())) or not cmd.RequiresAdmin():
					result = cmd.Try(self,query)
					if result['handled']:
						if 'debug' in result:
							self._lastDebug = {'message':result['debug'],'source':cmds}
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
		self._db = MySQLdb.connect(host=config('dbHost'),user=config('dbUser'),passwd=config('dbPass'),db=config('dbDB'))
	
	def db(self):
		if not self._db:
			self._connectDB()
		return self._db.cursor()
	
	
def main():	
	if len(sys.argv) > 1:
		configfile = sys.argv[1]
	else:
		configfile = 'pail.json'
	loadConfig(configfile)
	bot = Pail(config('nickname'), config('server'), config('port'))
	bot.start()

if __name__ == "__main__":
	main()
