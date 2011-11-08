from common import *
import re
import random
import copy

class Factory(CommandModuleFactory):
	def Commands(self):
		return {
			'giveitem':GiveItem()
		}
	
	def Exports(self):
		return {
			'builtinvar':[{	'inventory':self._inventory,
							'item':self._item,
							'aitem':self._aitem,
							'giveitem':self._giveitem,
							'agiveitem':self._agiveitem
				}]
		}
	
	def _inventory(self, bot, query):
		items = bot.getCommand('giveitem')._items.values()
		random.shuffle(items)
		text = ""
		for i in range(0,len(items)-1):
			it = items[i]
			print it
			r = random.randint(0,10)
			if r == 0:
				text += it['particle']+" "+it['name']+" from "+it['owner']+", "
			elif r == 1 and it['particle']=='this' or it['particle']=='lots of':
				text += it['name']+", "
			else:
				text += it['particle']+" "+it['name']+", "
		it = items[-1]
		text += "and " + it['particle']+" "+it['name']
		return text
	
	def _item(self,bot,query):
		item = pickOne(bot.getCommand('giveitem')._items.values())
		return item['name']
	
	def _aitem(self,bot,query):
		item = pickOne(bot.getCommand('giveitem')._items.values())
		return item['particle']+" "+item['name']
		
	def _giveitem(self,bot,query):
		item = pickOne(bot.getCommand('giveitem')._items.values())
		bot.getCommand('giveitem').DropItem(item['name'])
		return item['name']
	
	def _agiveitem(self,bot,query):
		item = pickOne(bot.getCommand('giveitem')._items.values())
		bot.getCommand('giveitem').DropItem(item['name'])
		return item['particle']+" "+item['name']
		
class GiveItem(BotCommand):
	def __init__(self):
		self._rx_action = []
		for r in [r"puts\s((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)\sin\s%(nick)s",
				r"(gives|hands)\s%(nick)s\s((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)",
				r"(gives|hands)\s((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)\sto\s%(nick)s"]:
			self._rx_action.append(re.compile(r%{'nick':config('nickname')},re.IGNORECASE))
		self._rx_directed = [re.compile(r"(take|have)\s((?P<particle>a|an|this)\s)?(?P<item>.+)")]
		self._items = None
		self._itemsCache = None
		
		self._hasItemFactoid = [{
			'trigger':'nothanks',
			'method':'reply',
			'response':'No thanks $who, I already have one'
		},
		{
			'trigger':'nothanks',
			'method':'reply',
			'response':'No thanks $who, I already have $aitem'
		}]
		
		self._maxItemCountFactoid = [{
			'trigger':'maxitems',
			'method':'action',
			'response':'takes $aitem and drops $agiveitem'
		},
		{
			'trigger':'maxitems',
			'method':'action',
			'response':'takes $aitem and gives $who $agiveitem in return'
		}]
		
		self._takeItemFactoid = [{
			'trigger':'takeitem',
			'method':'action',
			'response':'now contains $inventory'
		},
		{
			'trigger':'takeitem',
			'method':'action',
			'response':'now has $inventory in it'
		}]
		
	def Try(self,bot,query):
		if self._items is None:
			self._fillInventory(bot)
		if query.Directed():
			rx = self._rx_directed
		elif query.IsAction():
			rx = self._rx_action
		else:
			return {'handled':False}
		for m in rx:
			_match = m.match(query.Message())
			if not _match is None:
				break
		if _match:
			if _match.group('particle') == '':
				particle = "a"
			else:
				particle = _match.group('particle')
			item = {'name': _match.group('item'),
					'owner':nm_to_n(query.From()),
					'particle':particle}
			if self.HasItem(item['name']):
				f = pickOne(self._hasItemFactoid)
			elif len(self._items) == config('maxItems'):
				f = pickOne(self._maxItemCountFactoid)
				self.TakeItem(item,bot)
			else:
				f = pickOne(self._takeItemFactoid)
				self.TakeItem(item,bot)
			print self._processFactoid(f,item)
			bot.getCommand('factoidtrigger').sayFactoid(self._processFactoid(f,item),bot,query)
			resp = {'handled':True,'debug':'Got %(particle)s %(item)s from %(who)s'%{'item':item['name'],'who':nm_to_n(query.From()),'particle':item['particle']}}
			bot.log(resp['debug'])
			return resp
		return {'handled':False}
	
	
	def IgnoreActions(self):
		return False
	
	def _refreshItemCache(self,bot):
		self._itemsCache = {}
		for i in bot.sql("select name,owner,particle from bucket_items order by RAND() limit %s;",(config('maxItems')*5),['name','owner','particle']):
			self._itemsCache[i['name']]=i
	
	def _fillInventory(self, bot):
		self._refreshItemCache(bot)
		self._items={}
		if len(self._itemsCache) > config('initialItems'):
			for i in range(0,config('initialItems')):
				while True:
					i = self._itemsCache.values()[random.randint(0,len(self._itemsCache)-1)]
					if not self.HasItem(i['name']):
						self._items[i['name']]=i
						break
		else:
			self._items = self._itemsCache.values()[:]
				
				
	def HasItem(self, itemName):
		return itemName in self._items.keys()
		
	def TakeItem(self, item, bot):
		self._items[item['name']]=item
		bot.sql(r"delete from bucket_items where name=%s",(item['name']))
		bot.sql(r"insert into bucket_items (name,owner,particle) values (%s,%s,%s);",(item['name'],item['owner'],item['particle']))
	
	def DropItem(self, itemName):
		if self.HasItem(itemName):
			del self._items[itemName]
	
	def ForgetItem(self, itemName, bot):
		self._DropItem(itemName)
		if itemName in self._itemsCache.keys():
			del self._itemsCache[itemName]
		bot.sql(r"delete from bucket_items where name=%s",(item['name']))
		
	def _processFactoid(self, fact, item):
		f = copy.copy(fact)
		f['response'] = f['response'].replace('$aitem',item['particle']+" "+item['name'])
		f['response'] = f['response'].replace('$item',item['name'])
		return f