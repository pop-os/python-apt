
class DistUpgradeView(object):
    " abstraction for the upgrade view "
    def __init__(self):
        pass
    def getOpCacheProgress(self):
        " return a OpProgress() subclass for the given graphic"
        return apt.progress.OpProgress()
    def getFetchProgress(self):
        " return a fetch progress object "
        return apt.progress.FetchProgress()
    def getInstallProgress(self):
        " return a install progress object "
        return apt.progress.InstallProgress()
    def updateStatus(self, msg):
        """ update the current status of the distUpgrade based
            on the current view
        """
        pass
    def confirmChanges(self, changes, downloadSize):
        """ display the list of changed packages (apt.Package) and
            return if the user confirms them
        """
        self.toInstall = []
        self.toUpgrade = []
        self.toRemove = []
        for pkg in changes:
            if pkg.markedInstall: self.toInstall.append(pkg.name)
            elif pkg.markedUpgrade: self.toUpgrade.append(pkg.name)
            elif pkg.markedDelete: self.toRemove.append(pkg.name)
        # no downgrades, re-installs 
        assert(len(self.toInstall)+len(self.toUpgrade)+len(self.toRemove) == len(changes))
    def askYesNoQuestion(self, summary, msg):
        " ask a Yes/No question and return True on 'Yes' "
        pass
    def error(self, summary, msg):
        " display a error "
        pass
