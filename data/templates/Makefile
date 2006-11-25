
DOMAIN=update-manager
INFO_IN_FILES := $(wildcard *.info.in)
INFO_FILES := $(patsubst %.info.in,%.info,$(wildcard *.info.in))

all: $(INFO_FILES)

%.info: %.info.in 
	sed 's/^_//g' < $< > $@
	intltool-extract --type=gettext/rfc822deb $<
	#intltool-merge -d ../po $< $@

clean:
	rm -f $(wildcard *.h)
