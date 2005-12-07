
def str_to_bool(str):
  if str == "0" or str.upper() == "FALSE":
    return False
  return True

def utf8(str):
  return unicode(str, 'latin1').encode('utf-8')

