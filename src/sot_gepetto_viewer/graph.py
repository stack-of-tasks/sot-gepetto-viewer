from PythonQt.QGraphViz import QGVScene
from PythonQt import QtCore
from PythonQt import QtGui, Qt
from command_execution import CommandExecution
import time

class Graph:
    def __init__(self, plugin):
        self.plugin = plugin
        self.graph = QGVScene("graph")
        self.view = QtGui.QGraphicsView (self.graph)
        self.layoutShouldBeFreed = False
        self.graph.connect(Qt.SIGNAL("nodeMouseRelease(QGVNode*)"), self.updateLayout)
        self.graph.connect(Qt.SIGNAL("nodeContextMenu(QGVNode*)" ), self._nodeContextMenu)
        self.graph.connect(Qt.SIGNAL("edgeContextMenu(QGVEdge*)" ), self._signalContextMenu)
	self.graph.connect(Qt.SIGNAL("edgeContextMenu(QGVEdge*)" ), self._signalContextMenu)
	
	self.filter = "0"
        ### An object returned by re.compile
        self.entityFilter = None
        self.typeCallbacks = {
                "Task": ( self._nodeEntityTask, self._edgeEntityTask ),
                "SOT" : ( self._nodeEntitySOT , self._edgeEntitySOT  )
                }

        self.initCmd()

	self.LaunchRefresh()
	
	#self.createAllGraph()

    def clear (self):
        if self.layoutShouldBeFreed:
            self.graph.freeLayout()
            self.layoutShouldBeFreed = False
        self.nodes = {}
        self.types = {}
        self.edges = {}
        self.edgesBack = {}
        self.subgraphs = {}
        self.graph.clear()

    def initLayout (self):
        if self.layoutShouldBeFreed:
            self.graph.freeLayout()
        self.graph.applyLayout("dot")
        self.graph.setNodePositionAttribute()
        self.graph.setGraphAttribute("splines","spline")
        self.graph.setGraphAttribute("overlap","false")
        self.graph.setNodeAttribute ("pin","true")
        self.layoutShouldBeFreed = True

    def updateLayout (self):
        if self.layoutShouldBeFreed:
            self.graph.freeLayout()
        self.graph.applyLayout("nop2")
        self.layoutShouldBeFreed = True

    def initCmd (self):
        self.cmd = CommandExecution()

    def setEntityFilter (self, filter):
        self.entityFilter = filter
        #print self.entityFilter

    def RefreshAuto(self, e):
	print "test"
	#QTimer.singleShot(1000, self.essaie)

	#self.timer = QTimer()
	#self.timer.connect(timer, SIGNAL(timeout()), this, SLOT(self.essaie))
        #timer.start(1000)

	#timer = QTimer()
	#timer.timeout.connect(self.essaie)
	#timer.start(1000)

	

    def StopRefresh(self):
	self.timer.stop()
	print "Auto Refresh Stopped"

    def LaunchRefresh(self):
	print "Auto Refreshed Launched"
	self.timer = QtCore.QTimer()
	self.timer.connect(self.timer, QtCore.SIGNAL("timeout()"), self.createAllGraph)
        self.timer.start(1000)

    def createAllGraph (self):
        str_entities = self.cmd.run ("dg.entity.Entity.entities.keys()")
        self.clear()
	entities = eval(str_entities)
        for e in entities:
	    if self.filter == "0" or self.filter in e:
                if self.entityFilter is not None and not self.entityFilter.search(e):
                    continue
                etype = self.cmd.run("dg.entity.Entity.entities['"+e+"'].className")
                self.types[e] = etype
                if self.typeCallbacks.has_key(etype):
                    self.typeCallbacks[etype][0] (e)
                else:
                    self._nodeEntity(e)
        for e in entities:
	    if self.filter == "0" or self.filter in e:
                if self.entityFilter is not None and not self.entityFilter.search(e):
                    continue
                etype = self.types[e]
	    #if self.filter == "0":
                if self.typeCallbacks.has_key(etype):
                    self.typeCallbacks[etype][1] (e)
                else:
                    self._edgeEntitySignals (e)
        self.initLayout()

    def getNodeInformation (self, e):
	str_signals = self.cmd.run("[ s.name for s in dg.entity.Entity.entities['"+e+"'].signals() ]")
	signals = eval(str_signals)
	print (e)
	for s in signals:
            ss = s.split("::")
            if len(ss) != 3:
                print "Cannot handle", s
            elif ss[1].startswith("in"):
		print ss[2]

    def createGraphBackwardFromEntity (self, e):
        ok = self.cmd.run("dg.entity.Entity.entities.has_key('"+e+"')")
        if not ok:
            raise ValueError ("Entity " + e + " does not exist")
        self.clear()
        self._createGraphBackwardFromEntity (e)
        self.initLayout()

    def _createGraphBackwardFromEntity (self, e):
        etype = self.cmd.run("dg.entity.Entity.entities['"+e+"'].className")
        self.types[e] = etype
        if self.typeCallbacks.has_key(etype):
            self.typeCallbacks[etype][0] (e)
            self.typeCallbacks[etype][1] (e)
        else:
            self._nodeEntity(e)
            self._edgeEntitySignals (e)

    def _nodeEntitySOT(self, s):
        subgraph = self.graph.addSubGraph("Tasks in " + s, True) # True means "cluster"
        # subgraph.setAttribute("rank", "same")
        # subgraph.setAttribute("rank", "max")
        # subgraph.setAttribute("rankdir", "LR")
        subgraph.setAttribute("ranksep", "0.1")
        # print self.cmd.run("dg.entity.Entity.entities['"+s+"'].display()")
        tasks = eval(self.cmd.run("dg.entity.Entity.entities['"+s+"'].list()"))
        nodes = []
        for i, t in enumerate(tasks):
            node = subgraph.addNode (str(i))
            #TODO set properties
            nodes.append(node)
        # node = self.graph.addNode(s)
        node = subgraph.addNode(s)
        # node.setAttribute("rank", "max")
        self.nodes[s] = node
        for prev, node in zip(nodes,nodes[1:] + [node,]):
            edge = self.graph.addEdge (prev,node)
            # edge.setAttribute("constraint","false")
            #TODO set properties
        self.subgraphs[s] = (subgraph, tasks, nodes)
        # self._nodeEntity(s)

    def _edgeEntitySOT(self, s):
        subgraph, tasks, nodes = self.subgraphs[s]
        for t,n in zip(tasks, nodes):
            if not self.nodes.has_key(t):
                self._createGraphBackwardFromEntity(t)
	    if self.filter == "0":
            	e = self.graph.addEdge (self.nodes[t], n, "error")
            	# TODO errorTimeDerivative
            	n = "sot_" + s + "/task_" + t + "/error"
            	self.edges[n] = (t, e)
            	self.edgesBack[e] = n

    def _nodeEntityTask(self, t):
        self._nodeEntity(t)

    def _edgeEntityTask(self, t):
        # Build features list
        features = eval(self.cmd.run("dg.entity.Entity.entities['"+t+"'].list()"))
        for f in features:
            if not self.nodes.has_key(f):
                self._createGraphBackwardFromEntity(f)
	    if self.filter == "0" or (self.filter in f and self.filter in t):
            	edge = self.graph.addEdge (self.nodes[f], self.nodes[t])
            	# TODO set edge properties
            	edge.setAttribute("color", "red")
        self._edgeEntitySignals (t)
        pass

    def _nodeEntity(self, e):
	if self.filter == "0" or self.filter in e:
            self.nodes[e] = self.graph.addNode (e)


    def _edgeEntitySignals(self, e):
        str_signals = self.cmd.run("[ s.name for s in dg.entity.Entity.entities['"+e+"'].signals() ]")
	signals = eval(str_signals)
	for s in signals:
            ss = s.split("::")
            if len(ss) != 3:
                print "Cannot handle", s
            elif ss[1].startswith("in"):
                plugged = self.cmd.run("dg.entity.Entity.entities['"+e+"'].signal('"+ss[-1]+"').isPlugged()")
                other_s = self.cmd.run("dg.entity.Entity.entities['"+e+"'].signal('"+ss[-1]+"').getPlugged().name if dg.entity.Entity.entities['"+e+"'].signal('"+ss[-1]+"').isPlugged() else None")
                if other_s is not None and s != other_s:
                    idx = other_s.index('(')+1
                    other_e = other_s[idx:other_s.index(')',idx)]
		    if self.filter == "0" or (self.filter in other_e and self.filter in e):	
                        if not self.nodes.has_key(other_e):
                            self._createGraphBackwardFromEntity(other_e)
                    	self.edges[s] = (e, self.graph.addEdge (self.nodes[other_e], self.nodes[e], ss[2]))		#les noms sont la (e et other_e)
                    	self.edgesBack[self.edges[s][1]] = s
            elif ss[1].startswith("out"):
                pass
            else:
                print "unknown", s

    def _nodeContextMenu (self, node):
        e = node.getAttribute("label")
        if self.nodes.has_key(e):
            menu = QtGui.QMenu("Entity " + e, self.view)
            a = menu.addAction("Show graph backward")
            a.connect(Qt.SIGNAL("triggered()"), lambda: self.createGraphBackwardFromEntity(e))
	    menu.popup(QtGui.QCursor.pos())
	    b = menu.addAction("Test")
            b.connect(Qt.SIGNAL("triggered()"), lambda: self.getNodeInformation(e))
            menu.popup(QtGui.QCursor.pos())

    def _signalContextMenu (self, edge):
        s = edge.getAttribute("xlabel")
        if self.edgesBack.has_key(edge):
            e = self.edges[self.edgesBack[edge]][0]
            menu = QtGui.QMenu("Signal " + e, self.view)
            a = menu.addAction("Toggle display value")
            a.connect(Qt.SIGNAL("triggered()"), lambda: self.plugin.toggleDisplaySignalValue(e, s))
            menu.popup(QtGui.QCursor.pos())
        else:
            print edge
