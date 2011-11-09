import json

config = None

class Config:
	
	def __init__(self,file):
		self._loadConfig(file)
		self._defaults={}
	
	def __getitem__(self,key):
		if key in self._config:
			return self._config[key]
		elif key in self._defaults:
			return self._defaults[key]
	
	def __setitem__(self,key,item):
		self._config[key] = item
		self.saveConfig()
	
	def setDefault(self,key,default):
		self._defaults[key]=default

	def _loadConfig(self, file):
		self._configfile = file
		f = open(file,'r')
		self._config = json.load(f)
		f.close()
		
	def saveConfig(self):
		cfg = dict(self._config.items())
		for d in self._defaults.keys():
			if cfg[d] == self._defaults[d]:
				del cfg[d]
		stream = open(self._configfile,'w')
		json.dump(cfg,stream, sort_keys=True, indent=4)
		stream.close()