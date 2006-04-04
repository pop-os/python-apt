# This is a class which contains stubs for the gconf methods
# used in Update Manager. When gconf is unavailable it will
# still work but not retain the user settings.

class FakeGconf:

	def get_bool(self, key):
		return False 

	def set_bool(self, key,value):
		pass

	def get_pair(self, key, ta = None, tb = None):
		return [300,300] 
		
	def set_pair(self, key, ta, tb, a, b):
		pass

VALUE_INT = ""

def client_get_default():
	return  FakeGconf()


