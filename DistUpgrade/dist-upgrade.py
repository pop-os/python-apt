#!/usr/bin/python2.4

from DistUpgradeViewGtk import GtkDistUpgradeView
from DistUpgradeControler import DistUpgradeControler
import logging
import os

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.expanduser("~/dist-upgrade.log"),
                        format='%(asctime)s %(levelname)s %(message)s',
                        filemode='w')

    view = GtkDistUpgradeView()
    app = DistUpgradeControler(view)

    app.run()

    # testcode to see if the bullets look nice in the dialog
    #for i in range(4):
    #    view.setStep(i+1)
    #    app.openCache()
