from __future__ import print_function
from PythonQt import QtGui, Qt
from graph import Graph
from plot import Plot

hookRegistration = "from sot_gepetto_viewer.callback_after_robot_increment import CallbackRobotAfterIncrement"

class Plugin(QtGui.QDockWidget):
    def __init__(self, main):
        super(Plugin, self).__init__ ("Stack Of Tasks plugin", main)
        self.setObjectName("Stack Of Tasks plugin")
        self.main = main
        self.graph = Graph (self)
        self.plot = Plot (self)
        self.allFilter = ""

        self.tabWidget = QtGui.QTabWidget(self)
        self.setWidget (self.tabWidget)
        self.tabWidget.addTab (self.graph.view, "SoT graph")
        self.tabWidget.addTab (self.plot, "Plot")

        self.myQLineEdit = QtGui.QLineEdit("Type text here")

        toolBar = QtGui.QToolBar ("SoT buttons")
        toolBar.addAction(QtGui.QIcon.fromTheme("view-refresh"), "Create entire graph", self.graph.createAllGraph)
        toolBar.addSeparator()
        toolBar.addAction(QtGui.QIcon.fromTheme("zoom-fit-best"), "Zoom fit best", self.plot.zoomFitBest)
        toolBar.addAction(QtGui.QIcon.fromTheme("media-playback-stop"), "Stop fetching data", self.stopAnimation)
        toolBar.addSeparator()
        toolBar.addAction(QtGui.QIcon.fromTheme("window-new"), "Create viewer", self.createRobotView)
        toolBar.addSeparator()
        toolBar.addAction(QtGui.QIcon.fromTheme("view-filter"), "Set entity filter by name", self.entityFilterByName)
        toolBar.addSeparator()
        main.addToolBar (toolBar)
        toolBar2 = QtGui.QToolBar ("SoT buttons")
        toolBar2.addAction(QtGui.QIcon.fromTheme("Get Entity List"), "Get Entity List", self.graph.getList)
        toolBar2.addAction(QtGui.QIcon.fromTheme("Stop"), "Stop", self.graph.stopRefresh)
        toolBar2.addAction(QtGui.QIcon.fromTheme("Launch"), "Launch", self.graph.launchRefresh)
        toolBar2.addSeparator()
        toolBar2.addAction(QtGui.QIcon.fromTheme("add-filter"), "New Filter", self.addFilter)
        toolBar2.addAction(QtGui.QIcon.fromTheme("add-filter"), "Delete last Filter", self.rmvFilter)
        toolBar2.addSeparator()
        toolBar2.addWidget(self.myQLineEdit)
        toolBar2.addSeparator()
        toolBar2.addAction(QtGui.QIcon.fromTheme("Reset-filter"), "Reset Filter", self.resetFilter)
        main.addToolBar (toolBar2)

        self.displaySignals = []
        self.hookRegistered = False
        self.displaySignalValuesStarted = False

    def addFilter (self):
        block = False
        self.filter = self.myQLineEdit.text

        block = any( (self.filter in i for i in self.graph.filter) )

        if not block and self.filter not in self.allFilter:
            if self.allFilter == "0":
                self.allFilter = self.filter
            else :
                self.allFilter = self.allFilter + " " + self.filter

        self.myQLineEdit.clear()
        self.graph.updateFilter(self.allFilter)

    def rmvFilter (self):
        self.newFilter = self.allFilter.rsplit(' ', 1)[0]

        if self.allFilter == self.newFilter:
            self.newFilter = "0"

        self.graph.updateFilter(self.newFilter)

    def resetFilter (self):
        self.allFilter = "0"
        self.graph.updateFilter(self.allFilter)
	
    def createRobotView (self):
        from pinocchio import RobotWrapper, se3
        import os
        file = str(QtGui.QFileDialog.getOpenFileName(self, "Robot description file"))
        #print (file)
        # file = "/local/jmirabel/devel/openrobots/install/share/talos_data/robots/talos_reduced.urdf"
        self.robot = RobotWrapper (
                filename = file,
                package_dirs = os.getenv("ROS_PACKAGE_PATH", None),
                # package_dirs = [ "/local/jmirabel/devel/openrobots/install/share", ],
                root_joint = se3.JointModelFreeFlyer())
        self.robot.initDisplay()
        self.robot.loadDisplayModel("world/pinocchio")
        cmd = self.graph.cmd
        q = cmd.run("robot.dynamic.position.value")
        q = self._sotToPin (q)
        self.robot.display(q)

    def setFilter (self):
        try:
            ef = self.filter
        except:
            ef = ""
        self.filter = Qt.QInputDialog.getText(self, "Entity filter", "Filter entity by name", Qt.QLineEdit.Normal, ef)
        if len(self.filter) > 0:
            self.graph.filter = self.filter
        else:
            self.graph.filter = "0"

    def entityFilterByName (self):
        try:
            ef = self.entityFilter
        except:
            ef = ""
        self.entityFilter = Qt.QInputDialog.getText(self, "Entity filter", "Filter entity by name", Qt.QLineEdit.Normal, ef)

        if len(self.entityFilter) > 0:
            import re
            efre = re.compile (self.entityFilter)
            self.graph.setEntityFilter (efre)
        else:
            self.graph.setEntityFilter (None)

    def toggleDisplaySignalValue (self, entity, signal):
        #print ("Toggle"+ entity+ signal)
        k = (entity, signal)
        try:
            idx = self.displaySignals.index(k)
            self.plot.stopAnimation()
            self._dehookSignal(entity, signal)
            self.displaySignals.pop(idx)
        except ValueError:
            if not self.hookRegistered:
                self._registerHook()
                self.hookRegistered = True
            self._hookSignal(entity, signal)
            self.displaySignals.append(k)
        self.plot.initCurves (self.displaySignals)

    def stopAnimation (self):
        self.plot.stopAnimation()
        for k in self.displaySignals:
            self._dehookSignal (k[0], k[1])
        self.displaySignals = []

    def _sotToPin(self, q):
        # Handle the very annoying problem of RPY->quaternion
        # with the good convention...
        from dynamic_graph.sot.tools.quaternion import Quaternion
        import numpy as np
        quat = Quaternion()
        quat = tuple(quat.fromRPY(q[3], q[4], q[5]).array.tolist())
        return np.matrix(q[0:3] + quat[1:] + (quat[0],) + q[6:])

    def _createView (self, name):
        osg = self.main.createView (name)
        return osg.wid()

    def _registerHook (self):
        self.graph.cmd.run (hookRegistration,False)
        self.graph.cmd.run ("hook = CallbackRobotAfterIncrement()", False)
        self.graph.cmd.run ("hook.register()", False)

    def _hookSignal(self, entity, signal):
        self.graph.cmd.run ("hook.watchSignal('"+entity+"', '"+signal+"')", False)
    def _dehookSignal(self, entity, signal):
        self.graph.cmd.run ("hook.unwatchSignal('"+entity+"', '"+signal+"')", False)

    def _fetchNewSignalValues(self):
        values = self.graph.cmd.run ("hook.fetch()")
        return values

    def refreshInterface(self):
        self.graph.createAllGraph()
