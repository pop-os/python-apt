# Copyright (c) 2006 Jani Monoses  <jani@ubuntu.com>

# This is a class which handles settings when the gconf library
# is unavailable such as in a non-Gnome environment
# The configuration is stored in python hash format which is sourced
# at program start and dumped at exit

import string
import atexit

CONFIG_FILE="/root/.update-manager-conf"

class FakeGconf:
	
	def __init__(self):
		self.config = {}
		try:
			#execute python file which contains the dictionary called config
			exec open (CONFIG_FILE) 
			self.config = config
		except:
			pass

	#only get the 'basename' from the gconf key
	def keyname(self, key):
		return string.rsplit(key, '/', 1)[-1]
	
	def get_bool(self, key):
		key = self.keyname(key)
		return self.config.setdefault(self.keyname(key), True)

	def set_bool(self, key,value):
		key = self.keyname(key)
		self.config[key] = value

	# FIXME assume type is int for now
	def get_pair(self, key, ta = None, tb = None):
		key = self.keyname(key)
		return self.config.setdefault(self.keyname(key), [400, 500])
		
	# FIXME assume type is int for now
	def set_pair(self, key, ta, tb, a, b):
		key = self.keyname(key)
		self.config[key] = [a, b]

	#Save current dictionary to config file
	def save(self):
		file = open(CONFIG_FILE, "w")
		data = "config = {"
		for i in self.config:
			data +=  "'"+i+"'" + ":" + str(self.config[i])+",\n"
		data += "}"
		file.write(data)
		file.close()
		

VALUE_INT = ""

fakegconf = FakeGconf()

def client_get_default():
	return  fakegconf

def fakegconf_atexit():
	fakegconf.save()

atexit.register(fakegconf_atexit)


