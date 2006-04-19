import gtk

def str_to_bool(str):
  if str == "0" or str.upper() == "FALSE":
    return False
  return True

def utf8(str):
  return unicode(str, 'latin1').encode('utf-8')


def error(parent, summary, message):
  d = gtk.MessageDialog(parent=parent,
                        flags=gtk.DIALOG_MODAL,
                        type=gtk.MESSAGE_ERROR,
                        buttons=gtk.BUTTONS_CLOSE)
  d.set_markup("<big><b>%s</b></big>\n\n%s" % (summary, message))
  d.realize()
  d.window.set_functions(gtk.gdk.FUNC_MOVE)
  d.set_title("")
  res = d.run()
  d.destroy()
  return
