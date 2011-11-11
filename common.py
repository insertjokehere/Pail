from irclib import nm_to_n
import re
import random
import cfg



def pickOne(list):
	r = random.randint(0,len(list)-1)
	return list[r]
	
def isAdmin(username):
	return nm_to_n(username) in cfg.config['admins']

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

class CommandModuleFactory:
	def __init__(self,bot):
		self._bot = bot
		
	def Commands(self):
		return {}
	
	def Exports(self):
		return {}
	
	def Defaults(self):
		return {}
	
	def TimerFunctions(self):
		return []
		
class BotCommand:
	def RequiresAdmin(self):
		return False
	
	def IgnoreActions(self):
		return True
		
	def Try(self, bot, query):
		return self.Unhandled()

	def OK(self,bot,query):
		bot.say(query,"Ok, %(who)s" % {'who':nm_to_n(query.From())})
	
	def Unhandled(self):
		return {'handled':False}
		
	def Handled(self,debug=""):
		return {'handled':True,'debug':debug}

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
				if _match.group('id')[0] == "#": #delete by id number, otherwise by key
					id=_match.group('id')[1:]
					entry = bot.sql(r'select name,protected from %(table)s where id=%%s'%{'table':self._table},(id),['key','protected'])[0] #id is the primary key, so there will only be one tupple returned
					if (entry['protected']==1 and isAdmin(query.From())) or entry['protected'] == 0:
						self._clearCache(bot,entry['key'])
						bot.sql(r'delete from %(table)s where id=%%s'%{'table':self._table},(id))
						self.OK(bot,query)
						resp = self.Handled('deleted %(type)s #%(num)s for %(who)s'%{'type':self._type,'num':id,'who':nm_to_n(query.From())})
					else:
						bot.say(query,"Sorry %(who)s, that %(type)s is protected"%{'who':nm_to_n(query.From()),'type':self._type})
						resp = self.Handled('%(who)s attempted to delete protected %(type)s #%(num)s'%{'who':query.From(),'num':id,'type':self._type})
				elif isAdmin(query.From()): #batch delete, requires admin
					key=_match.group('id')
					bot.sql('delete from %(table)s where name=%%s'%{'table':self._table},(key))
					self._clearCache(bot, key)
					self.OK(bot,query)
					resp=self.Handled("deleted %(type)s '%(key)s' for %(who)s"%{'type':self._type,'who':query.From(),'key':key})
				else:
					bot.say(query,"Sorry %(who)s, you need to be an admin to do that"%{'who':nm_to_n(query.From())})
					resp = self.Handled("%(who)s attempted to batch delete factoid '%(key)s'"%{'who':query.From(),'key':key})
				bot.log(resp['debug'])
				return resp
		return self.Unhandled()

class ProtectCommand(BotCommand):
	def __init__(self, name, regex, table):
		self._rx = re.compile(regex,re.IGNORECASE)
		self._name = name
		self._table = table
	
	def RequiresAdmin(self):
		return True
	
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				if _match.group('mode').lower().startswith('un'):
					mode = 0
				else:
					mode = 1
				if _match.group('key').startswith('#'):
					key='id'
					id=_match.group('key')[1:]
					resp = self.Handled("%(who)s %(mode)sed %(type)s #%(id)s"%{'who':nm_to_n(query.From()),'mode':_match.group('mode').lower(),'type':self._name,'id':id})
				else:
					key='name'
					id = _match.group('key')
					resp = self.Handled("%(who)s batch %(mode)sed %(type)s '%(id)s'"%{'who':nm_to_n(query.From()),'mode':_match.group('mode').lower(),'type':self._name,'id':id})
				bot.sql(r'update %(table)s set protected=%%s where %(key)s=%%s'%{'table':self._table,'key':key},(mode,id))
				self.OK(bot,query)
				bot.log(resp['debug'])
				return resp
		return self.Unhandled()