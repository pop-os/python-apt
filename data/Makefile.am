@INTLTOOL_DESKTOP_RULE@

datadir=$(prefix)/share/update-manager
data_DATA=update-manager.glade \
	logo.png \
	SoftwareProperties.glade \
	SoftwarePropertiesDialogs.glade \
	update-manager.png

desktopdir = $(prefix)/share/applications
desktop_in_files = update-manager.desktop.in \
				   gnome-software-properties.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)

appicondir = $(prefix)/share/pixmaps
appicon_DATA = update-manager.png 


EXTRA_DIST= $(data_DATA) $(appicon_DATA) $(desktop_in_files)

CLEANFILES = $(desktop_DATA)
