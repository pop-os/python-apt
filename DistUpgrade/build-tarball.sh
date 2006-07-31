#!/bin/sh

DIST=edgy

# cleanup
rm -f *~ *.bak *.pyc *.moved '#'*

# update po
(cd ../po; make update-po)

# copy the mo files
cp -r ../po/mo .

# make symlink
if [ ! -h $DIST ]; then
	ln -s dist-upgrade.py $DIST
fi

# create the tarball, copy links in place 
tar -c -h -z -v --exclude=$DIST.tar.gz --exclude=$0 -f $DIST.tar.gz .


