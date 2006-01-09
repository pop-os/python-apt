#!/usr/bin/python2.4

from DistUpgradeViewGtk import GtkDistUpgradeView
from DistUpgradeControler import DistUpgradeControler
import logging

if __name__ == "__main__":

    view = GtkDistUpgradeView()
    app = DistUpgradeControler(view)

    logging.basicConfig(level=logging.DEBUG,
                        filename=os.path.expanduser("~/dist-upgrade.log"),
                        filemode='w')
    app.run()

    # testcode to see if the bullets look nice in the dialog
    #for i in range(4):
    #    view.setStep(i+1)
    #    app.openCache()
