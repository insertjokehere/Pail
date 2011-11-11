from common import *
import re
import random
import copy
import cfg

class Factory(CommandModuleFactory):
	def Commands(self):
		return {
			'giveitem':GiveItem(),
			'dropitem':DropItem(),
			'forgetitem':ForgetItem()
		}
	
	def Exports(self):
		return {
			'builtinvar':[{	'inventory':self._inventory,
							'item':self._item,
							'giveitem':self._giveitem
				}],
			'randomtrigger':[{'givebackitem':self._givebackitem}],
			'specialfactoid':['giveback','nothanks','maxitems','takeitem']
		}
	
	def Defaults(self):
		return {
			"maxItems":8,
			"initialItems":4,
			"minItems":2
		}
	
	def TimerFunctions(self):
		return [{'interval':60*60*2, #2 hours
				'function':self._refreshinventory}]
	
	def _inventory(self, bot, query):
		items = bot.getCommand('giveitem')._items.values()
		random.shuffle(items)
		text = ""
		for i in range(0,len(items)-1):
			it = items[i]
			r = random.randint(0,10)
			if r == 0 and not it['particle'] is None:
				text += it['particle']+" "+it['name']+" from "+it['owner']+", "
			elif r==0:
				text += it['name']+" from "+it['owner']+", "
			elif r == 1 and it['particle']=='this' or it['particle']=='lots of':
				text += it['name']+", "
			elif it['particle'] is None:
				text += it['name']+", "
			else:
				text += it['particle']+" "+it['name']+", "
		it = items[-1]
		if len(items)>1:
			text += "and "
		if it['particle'] is None:
			text +=  it['name']
		else:
			text += it['particle']+" "+it['name']
		return text
	
	def _item(self,bot,query):
		item = copy.copy(pickOne(bot.getCommand('giveitem')._items.values()))
		item['_'] = item['name']
		return item
	
	def _aitem(self,bot,query):
		item = pickOne(bot.getCommand('giveitem')._items.values())
		if item['particle'] is None:
			return item['name']
		else:
			return item['particle']+" "+item['name']
		
	def _giveitem(self,bot,query):
		item = copy.copy(pickOne(bot.getCommand('giveitem')._items.values()))
		bot.getCommand('giveitem').DropItem(item['name'])
		item['_'] = item['name']
		return item
	
	def _agiveitem(self,bot,query):
		item = pickOne(bot.getCommand('giveitem')._items.values())
		bot.getCommand('giveitem').DropItem(item['name'])
		if item['particle'] is None:
			return item['name']
		else:
			return item['particle']+" "+item['name']
		
	def _refreshinventory(self,args):
		self._bot.log("Refreshing item cache")
		self._bot.getCommand('giveitem')._refreshItemCache(self._bot)

	def _givebackitem(self, bot, query):
		bot.getCommand('factoidtrigger').triggerFactoid('giveback',bot,query)
	
class ForgetItem(BotCommand):
	def __init__(self):
		self._rx = re.compile(r'(forget|delete)\sitem\s((?P<particle>a|an|this|some|lots of)\s)?(?P<itemname>.+)',re.IGNORECASE)
		
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				giveitem = bot.getCommand('giveitem')
				if giveitem._items is None:
					giveitem._fillInventory(bot)
				itemname = _match.group('itemname')
				giveitem.ForgetItem(itemname,bot)
				resp = self.Handled('forgot item %(item)s for %(who)s'%{'item':itemname,'who':nm_to_n(query.From())})
				self.OK(bot,query)
				bot.log(resp['debug'])
				return resp
		return self.Unhandled()
		
	def RequiresAdmin(self):
		return True
	
class DropItem(BotCommand):
	def __init__(self):
		self._rx = re.compile(r"drop\s(item\s)?((?P<particle>a|an|this|some|lots of)\s)?(?P<itemname>.+)",re.IGNORECASE)
	
	def Try(self,bot,query):
		if query.Directed():
			_match = self._rx.match(query.Message())
			if _match:
				giveitem = bot.getCommand('giveitem')
				#todo: wrap this behavior in GiveItem
				if giveitem._items is None:
					giveitem._fillInventory(bot)
				itemname = _match.group('itemname')
				if itemname=="something":
					item = pickOne(giveitem._items.values())
				elif itemname in giveitem._items:
					item = giveitem._items[itemname]
				else:
					return self.Unhandled()
				giveitem.DropItem(item['name'])
				f = pickOne(giveitem._takeItemFactoid)
				bot.getCommand('factoidtrigger').sayFactoid(giveitem._processFactoid(f,item),bot,query)
				resp = self.Handled('Dropped %(item)s for %(who)s'%{"item":itemname,"who":nm_to_n(query.From())})
				bot.log(resp['debug'])
				return resp
		return self.Unhandled()
		
class GiveItem(BotCommand):
	def __init__(self):
		self._rx_action = []
		for r in [r"puts\s((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)\sin\s%(nick)s",
				r"(gives|hands)\s%(nick)s\s((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)",
				r"(gives|hands)\s((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)\sto\s%(nick)s"]:
			self._rx_action.append(re.compile(r%{'nick':cfg.config['nickname']},re.IGNORECASE))
		self._rx_directed = [re.compile(r"(take|have)\s((?P<particle>a|an|this)\s)?(?P<item>.+)")]
		self._items = None
		self._itemsCache = None
		
	def Try(self,bot,query):
		if self._items is None:
			self._fillInventory(bot)
		if query.Directed():
			rx = self._rx_directed
		elif query.IsAction():
			rx = self._rx_action
		else:
			return self.Unhandled()
		for m in rx:
			_match = m.match(query.Message())
			if not _match is None:
				break
		if _match:
			if _match.group('particle') == '':
				particle = ""
			else:
				particle = _match.group('particle')
			item = {'_':_match.group('item'),
					'name': _match.group('item'),
					'owner':nm_to_n(query.From()),
					'particle':particle}
			if self.HasItem(item['name']):
				f = 'nothanks'
				this=item
			elif len(self._items) == cfg.config['maxItems']:
				f = 'maxitems'
				self.TakeItem(item,bot)
				this = item
			else:
				f = 'takeitem'
				this = item
				self.TakeItem(item,bot)
			bot.getCommand('factoidtrigger').triggerFactoid(f,bot,query,this=this)
			resp = self.Handled('Got %(particle)s %(item)s from %(who)s'%{'item':item['name'],'who':nm_to_n(query.From()),'particle':item['particle']})
			bot.log(resp['debug'])
			return resp
		return self.Unhandled()
	
	
	def IgnoreActions(self):
		return False
	
	def _refreshItemCache(self,bot):
		self._itemsCache = {}
		for i in bot.sql("select name,owner,particle from pail_items order by RAND() limit %s;",(cfg.config['maxItems']*5),['name','owner','particle']):
			self._itemsCache[i['name']]=i
	
	def _fillInventory(self, bot):
		self._refreshItemCache(bot)
		self._items={}
		if len(self._itemsCache) > cfg.config['initialItems']:
			self.GetRandomItem(cfg.config['initialItems'])
		else:
			self._items = self._itemsCache.values()[:]
	
	def GetRandomItem(self,count=1):
		for i in range(0,count):
				while True:
					i = self._itemsCache.values()[random.randint(0,len(self._itemsCache)-1)]
					if not self.HasItem(i['name']):
						self._items[i['name']]=i
						break
				
	def HasItem(self, itemName):
		return itemName in self._items.keys()
		
	def TakeItem(self, item, bot):
		self._items[item['name']]=item
		bot.sql(r"delete from pail_items where name=%s",(item['name']))
		bot.sql(r"insert into pail_items (name,owner,particle) values (%s,%s,%s);",(item['name'],item['owner'],item['particle']))
	
	def DropItem(self, itemName):
		if self.HasItem(itemName):
			del self._items[itemName]
		if len(self._items) < cfg.config['minItems']:
			self.GetRandomItem()
	
	def ForgetItem(self, itemName, bot):
		self.DropItem(itemName)
		if itemName in self._itemsCache.keys():
			del self._itemsCache[itemName]
		bot.sql(r"delete from pail_items where name=%s",(itemName))
		