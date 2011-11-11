"""
Database port tool
Attempts to copy factoids and items from a Bucket database into a pail database
the target database must exist (import pail.sql), and access must be configured
in the config file

python portDB.py <configfile> <oldDB>
eg:
python portDB.py pail.json Bucket

ensure you have a backup before running
"""

import MySQLdb
import cfg
from common import *
import sys
import re

def main():
	if not len(sys.argv) == 3:
		exit()
	configfile = sys.argv[1]
	oldDB = sys.argv[2]
	cfg.config = cfg.Config(configfile)
	oldDB = MySQLdb.connect(host=cfg.config['dbHost'],user=cfg.config['dbUser'],passwd=cfg.config['dbPass'],db=oldDB)
	newDB = MySQLdb.connect(host=cfg.config['dbHost'],user=cfg.config['dbUser'],passwd=cfg.config['dbPass'],db=cfg.config['dbDB'])
	
	port_vars(oldDB.cursor(),newDB.cursor())
	port_factoids(oldDB.cursor(),newDB.cursor())
	port_items(oldDB.cursor(),newDB.cursor())
	
	newDB.commit()

def port_vars(oldDB,newDB):
	print "Porting variables"
	oldDB.execute(r"select name,value from bucket_vars join bucket_values on bucket_vars.id=bucket_values.var_id;")
	values = tuppleToList(['name','value'],oldDB.fetchall())
	print "Found %(count)d variable values"%{'count':len(values)}
	for v in values:
		newDB.execute(r"insert into pail_vars values(%s, %s, 0,0);",(v['name'],v['value']))
	print "DONE"

def port_factoids(oldDB,newDB):
	print "Porting factoids"
	oldDB.execute(r"select fact,verb,tidbit,protected from bucket_facts;")
	values = tuppleToList(['fact','verb','tidbit','protected'],oldDB.fetchall())
	print "Found %(count)d factoids"%{'count':len(values)}
	for v in values:
		if v['verb'].startswith('<') and v['verb'].endswith('>'):
			v['verb'] = v['verb'][1:-1]
		newDB.execute(r"insert into pail_facts values(%s, %s, %s, 0, %s)",(v['fact'],v['verb'],v['tidbit'],v['protected']))
	print "DONE"

def port_items(oldDB,newDB):
	rx = re.compile(r"((?P<particle>a|an|this|some|lots of)\s)?(?P<item>.+)",re.IGNORECASE)
	print "Porting items"
	oldDB.execute(r"select what,user from bucket_items")
	values = tuppleToList(['what','user'],oldDB.fetchall())
	print "Found %(count)d items"%{'count':len(values)}
	for v in values:
		_match = rx.match(v['what'])
		v['what']=_match.group('item')
		v['particle']=_match.group('particle')
		newDB.execute(r"insert into pail_items values(%s, %s, %s)",(v['what'],v['user'],v['particle']))
	print "DONE"
	
if __name__ == "__main__":
	main()
