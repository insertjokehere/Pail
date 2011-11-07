from irclib import nm_to_n
import re
import json
import random

_config = {}
_configfile = ""	

def config(key):
	return _config[key]

def loadConfig(file):
	global _configfile,_config
	_configfile = file
	f = open(file,'r')
	_config = json.load(f)
	f.close()
	
def saveConfig():
	stream = open(_configfile,'w')
	json.dump(config,stream, sort_keys=True, indent=4)
	stream.close()
	
def isAdmin(username):
	global config
	return nm_to_n(username) in config('admins')

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

class BotCommand:
	def RequiresAdmin(self):
		return False
		
	def Try(self, bot, query):
		return {'handled':False}

	def OK(self,bot,query):
		c=bot.connection
		c.privmsg(query.RespondTo(),"Ok, %(who)s" % {'who':nm_to_n(query.From())})

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
				cursor=bot.db()
				if _match.group('mode').lower().startswith('un'):
					mode = 0
				else:
					mode = 1
				if _match.group('key').startswith('#'):
					key='id'
					id=_match.group('key')[1:]
					resp = {'handled':True,'debug':"%(who)s %(mode)sed %(type)s #%(id)s"%{'who':nm_to_n(query.From()),'mode':_match.group('mode').lower(),'type':self._name,'id':id}}
				else:
					key='name'
					id = _match.group('key')
					resp = {'handled':True,'debug':"%(who)s batch %(mode)sed %(type)s '%(id)s'"%{'who':nm_to_n(query.From()),'mode':_match.group('mode').lower(),'type':self._name,'id':id}}
				cursor.execute(r'update %(table)s set protected=%%s where %(key)s=%%s'%{'table':self._table,'key':key},(mode,id))
				cursor.close()
				self.OK(bot,query)
				bot.log(resp['debug'])
				return resp
		return {'handled':False}