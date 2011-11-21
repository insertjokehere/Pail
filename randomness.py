from common import *
from pail import IrcQuery
import re
import random
import cfg
import datetime

class Factory(CommandModuleFactory):

	def Commands(self):
		return {
			'trigger':Trigger()
		}
	
	def Defaults(self):
		return {
			"randomTriggerInterval":60*5, #5 minutes,
			"randomTriggerChance":50, #1 in 50, so triggers once every ~4 hours
			"triggerBananas":True,
			"minNonIdleTime":60*2
		}
	
	def Exports(self):
		e = []
		if cfg.config['triggerBananas']:
			e.append({'bananas':self._bananas})
		return {'randomtrigger':e,'specialfactoid':'bananas'}
	
	def TimerFunctions(self):
		return [{'interval':cfg.config['randomTriggerInterval'],
				'function':self._dorandom}]
				
	def _dorandom(self,args):
		for ch in self._bot.channels.keys():
			if not ch == cfg.config['logChannel']:
				delta = None
				if not self._bot.lastMessageTime(ch) is None:
					delta = datetime.datetime.now() - self._bot.lastMessageTime(ch)
				if delta is None or delta >= datetime.timedelta(seconds=cfg.config['minNonIdleTime']):
					r = random.randint(0,cfg.config["randomTriggerChance"])
					if r == 0:
						q = IrcQuery('',ch,'',channel=ch)
						self._bot.getCommand('trigger')._trigger(self._bot, q)
				else:
					self._bot.log("supressing randomness due to channel idle")
	
	def _bananas(self, bot, query):
		bot.getCommand('factoidtrigger').triggerFactoid('bananas',bot,query)
	
class Trigger(BotCommand):

	def __init__(self):
		self._rx = re.compile(r"trigger\s(?P<trigger>\w+)",re.IGNORECASE)
	
	def Try(self,bot,query):
		if query.Directed():
			_match=self._rx.match(query.Message())
			if _match:
				triggername = _match.group('trigger')
				if self._trigger(bot,query, triggername):
					resp = self.Handled('Triggered %(trigger)s for %(who)s'%{'trigger':triggername,'who':nm_to_n(query.From())})
				else:
					bot.say(query,"I'm sorry %(who)s, I don't have a trigger by that name"%{'who':nm_to_n(query.From())})
					resp = self.Handled("%(who)s tried to trigger unknown trigger '%(trigger)s'"%{'who':nm_to_n(query.From()),'trigger':triggername})
				return resp
		return self.Unhandled()

	def RequiresAdmin(self):
		return True
	
	def _trigger(self, bot, to, name=""):
		triggers = {}
		for t in bot.getExport('randomtrigger'):
			for i in t.keys():
				triggers[i] = t[i]
		
		if len(triggers) == 0:
			return False
		if name == "":
			trigger = triggers[pickOne(triggers.keys())]
		elif name in triggers:
			trigger = triggers[name]
		else:
			return False
		trigger(bot, to)
		return True