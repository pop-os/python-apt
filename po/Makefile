
DOMAIN=update-manager
PO_FILES := $(wildcard *.po)

update-po: $(DOMAIN).pot $(patsubst %.po,%.mo,$(wildcard *.po))
	# update the po files 
	for f in $(PO_FILES); do \
		intltool-update -r $${f%.po}  -g $(DOMAIN); \
	done

$(DOMAIN).pot:
	intltool-update -p -g $(DOMAIN)

%.mo : %.po
	mkdir -p mo/$(subst .po,,$<)/LC_MESSAGES/ 
	msgfmt $< -o mo/$(subst .po,,$<)/LC_MESSAGES/$(DOMAIN).mo 
