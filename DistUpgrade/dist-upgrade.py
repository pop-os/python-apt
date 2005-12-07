#!/usr/bin/python2.4

from DistUpgradeViewGtk import GtkDistUpgradeView
from DistUpgradeControler import DistUpgradeControler

if __name__ == "__main__":
    view = GtkDistUpgradeView()
    app = DistUpgradeControler(view)
    app.run()

    # testcode to see if the bullets look nice in the dialog
    #for i in range(4):
    #    view.setStep(i+1)
    #    app.openCache()
