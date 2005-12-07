#!/usr/bin/python2.4

from DistUpgradeViewGtk import GtkDistUpgradeView
from DistUpgradeControler import DistUpgradeControler

if __name__ == "__main__":
    view = GtkDistUpgradeView()
    app = DistUpgradeControler(view)
    app.run()
