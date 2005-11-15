%.info: %.info.in
	sed 's/^_//g' < $< > $@
	$(INTLTOOL_EXTRACT) --type=gettext/rfc822deb $<

datadir=$(prefix)/share/update-manager
dinfodir = $(datadir)/dists
dinfo_DATA = Debian.info Ubuntu.info

EXTRA_DIST= $(dinfo_DATA)

CLEANFILES = $(dinfo_DATA) $(dinfo_DATA:.info=.info.in.h)
