import gtk

def dialog_error(parent, primary, secondary):
    p = "<span weight=\"bold\" size=\"larger\">%s</span>" % primary
    dialog = gtk.MessageDialog(parent,gtk.DIALOG_MODAL,
                               gtk.MESSAGE_ERROR,gtk.BUTTONS_OK,"")
    dialog.set_markup(p);
    dialog.format_secondary_text(secondary);
    dialog.run()
    dialog.hide()
