#!/usr/bin/env python
import apt_pkg

Parse = apt_pkg.ParseTagFile(open("apt/lists/_org_ftp.debian.org_ftp_dists_potato_main_binary-i386_Packages","r"));

while Parse.Step() == 1:
   print Parse.Section.get("Package");
   print apt_pkg.ParseDepends(Parse.Section.get("Depends",""));
