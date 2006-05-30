#!/usr/bin/python2.4

from DistUpgradeControler import DistUpgradeControler
from DistUpgradeConfigParser import DistUpgradeConfig
import logging
import os
import sys

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG,
                        filename="/var/log/dist-upgrade.log",
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w')

    config = DistUpgradeConfig()
    requested_view= config.get("View","View")
    try:
        view_modul = __import__(requested_view)
        view_class = getattr(view_modul, requested_view)
        view = view_class()
    except (ImportError, AttributeError):
        logging.error("can't import view '%s'" % requested_view)
        print "can't find %s" % requested_view
        sys.exit(1)
    app = DistUpgradeControler(view)

    app.run()

    # testcode to see if the bullets look nice in the dialog
    #for i in range(4):
    #    view.setStep(i+1)
    #    app.openCache()
