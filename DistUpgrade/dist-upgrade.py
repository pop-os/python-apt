#!/usr/bin/python2.4

from DistUpgradeControler import DistUpgradeControler
from DistUpgradeConfigParser import DistUpgradeConfig
import logging
import os
import os.path
import sys

if __name__ == "__main__":

    # init logging
    logging.basicConfig(level=logging.DEBUG,
                        filename="/var/log/dist-upgrade.log",
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w')

    # make sure we run under a segv-handler
    if not os.environ.has_key("LD_PRELOAD") or \
           not "libSegFault" in os.environ["LD_PRELOAD"]:
        fd = os.open("/var/log/dist-upgrade-segv.log",
                     os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        os.dup2(fd,1)
        os.dup2(fd,2)
        # restart ourself
        os.execl("/usr/bin/catchsegv", "catchsegv", sys.argv[0])
    else:
        logging.debug("Runing with segv-handler: %s", os.environ["LD_PRELOAD"])

    # init config and get a view
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
