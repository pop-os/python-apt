#!/usr/bin/python2.4

from DistUpgradeControler import DistUpgradeControler
from DistUpgradeConfigParser import DistUpgradeConfig
import logging
import os
import sys
from optparse import OptionParser

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--cdrom", dest="cdromPath", default=None,
                      help="Use the given path to search for a cdrom with upgradable packages")
    (options, args) = parser.parse_args()

    if not os.path.exists("/var/log/dist-upgrade"):
        os.mkdir("/var/log/dist-upgrade")
    logging.basicConfig(level=logging.DEBUG,
                        filename="/var/log/dist-upgrade/main.log",
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w')

    config = DistUpgradeConfig(".")
    requested_view= config.get("View","View")
    try:
        view_modul = __import__(requested_view)
        view_class = getattr(view_modul, requested_view)
        view = view_class()
    except (ImportError, AttributeError):
        logging.error("can't import view '%s'" % requested_view)
        print "can't find %s" % requested_view
        sys.exit(1)
    app = DistUpgradeControler(view, cdromPath=options.cdromPath)

    app.run()

    # testcode to see if the bullets look nice in the dialog
    #for i in range(4):
    #    view.setStep(i+1)
    #    app.openCache()
