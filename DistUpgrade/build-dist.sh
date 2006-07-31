#!/bin/sh

# build a tarball that is ready for the upload. the format is 
# simple, it contans:
#   $version/$dist.tar.gz 
#   $version/ReleaseNotes 
# this put into a file called "$dist-upgrader_$version.tar.gz"       


TARGETDIR=../dist-upgrade-build
SOURCEDIR=`pwd`
DIST=edgy
MAINTAINER="Michael Vogt <michael.vogt@ubuntu.com>"
NOTES=ReleaseAnnouncement
version=$(date +%Y%m%d.%H%M)

# create targetdir
if [ ! -d $TARGETDIR/$version ]; then
	mkdir -p $TARGETDIR/$version
fi

#build the actual dist-upgrader tarball
./build-tarball.sh

# how move it into a container including the targetdir (with version)
# and ReleaeNotes
cd $TARGETDIR/$version
cp $SOURCEDIR/$NOTES .
cp $SOURCEDIR/$DIST.tar.gz .
cd ..

# build it
TARBALL="dist-upgrader_"$version"_all.tar.gz"
tar czvf $TARBALL $version

# now create a changes file
CHANGES="dist-upgrader_"$version"_all.changes"
echo > $CHANGES
echo "Origin: Ubuntu/$DIST" >> $CHANGES 
echo "Format: 1.7" >> $CHANGES
echo "Date: `date -R`" >> $CHANGES
echo "Architecture: all">>$CHANGES
echo "Version: $version" >>$CHANGES
echo "Distribution: $DIST"  >>$CHANGES
echo "Source: dist-upgrader" >> $CHANGES
echo "Binary: dist-upgrader" >> $CHANGES
echo "Urgency: low" >> $CHANGES
echo "Maintainer: $MAINTAINER" >> $CHANGES
echo "Changed-By: $MAINTAINER" >> $CHANGES
echo "Changes: "  >> $CHANGES
echo " * new upstream version"  >> $CHANGES 
echo "Files: " >> $CHANGES
echo " `md5sum $TARBALL | awk '{print $1}'` `stat --format=%s $TARBALL` raw-dist-upgrader - $TARBALL" >> $CHANGES
