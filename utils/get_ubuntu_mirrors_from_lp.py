#!/usr/bin/python

import feedparser
import sys

#d = feedparser.parse("https://launchpad.net/ubuntu/+archivemirrors-rss")
d = feedparser.parse(open("+archivemirrors-rss"))

countries = {}

for entry in d.entries:
    countrycode = entry.mirror_countrycode
    if not countrycode in countries:
        countries[countrycode] = set()
    for link in entry.links:
        countries[countrycode].add(link.href)


keys = countries.keys()
keys.sort()
for country in keys:
    print "#LOC:%s" % country
    print "\n".join(countries[country])
