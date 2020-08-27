from __future__ import print_function
from PythonQt.QGraphViz import QGVScene
from PythonQt import QtCore
from PythonQt.QtCore import QThreadPool, QRunnable
from PythonQt import QtGui, Qt
from PythonQt.QtGui import QMessageBox
from command_execution import CommandExecution


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

    def StopRefresh(self):
        self.timer.stop()
        print ("Auto Refresh Stopped")

    def LaunchRefresh(self):
        print ("Auto Refreshed Launched")
        self.timer = QtCore.QTimer()
        self.timer.connect(self.timer, QtCore.SIGNAL("timeout()"), self.createAllGraph)
        self.timer.start(1000)
    
    def UpdateFilter (self, filt):
        self.filter = filt.split()

    def getList (self):
        import dynamic_graph
        from dynamic_graph.sot.core.robot_simu import RobotSimu

        chaine = "\n".join(dynamic_graph.entity.Entity.entityClassNameList)
        
        # Show the list of entities used with QMessageBox
        QMessageBox.information(None, "Entity list",chaine,
                        QMessageBox.Ok,
                        QMessageBox.Ok)


    def createAllGraph (self):
        self.EntityBlocked =""                 #Block the creation of any duplicate for entities or signals
        self.SignalBlocked =""
        entities = eval(self.cmd.run ("dg.entity.Entity.entities.keys()"))
        self.clear()

        ent_list = entities
        for e in ent_list:
            for i in self.filter:
                if i != "0" and i not in e:
                    continue
                if self.entityFilter is not None and not self.entityFilter.search(e):
                    continue
                etype = self.cmd.run("dg.entity.Entity.entities['"+e+"'].className")
                self.types[e] = etype
                if self.typeCallbacks.has_key(etype):
                    self.typeCallbacks[etype][0] (e)
                else:
                    self._nodeEntity(e)
                break


        ent_list = entities
        for e in ent_list:
            for j in self.filter:
                if j != "0" and j not in e:
                    continue
                if self.entityFilter is not None and not self.entityFilter.search(e):
                    continue
                etype = self.cmd.run("dg.entity.Entity.entities['"+e+"'].className")
                self.types[e] = etype
                if self.typeCallbacks.has_key(etype):
                    self.typeCallbacks[etype][1] (e)
                else:
                    self._edgeEntitySignals(e)
                break

        self.initLayout()

    def getNodeInformation (self, e):
        signals = eval(self.cmd.run("[ s.name for s in dg.entity.Entity.entities['"+e+"'].signals() ]"))
        chaine = "\n"
        for s in signals:
            ss = s.split("::")
            if len(ss) != 3:
                print ("Cannot handle"+ s)
            elif ss[1].startswith("in"):
                InfType = ss[1]
                text = InfType[ InfType.find( '(' )+1 : InfType.find( ')' ) ]
                chaine = chaine +"input : "+ ss[2] + ", type :" +text + "\n"
            elif ss[1].startswith("out"):
                InfType = ss[1]
                text = InfType[ InfType.find( '(' )+1 : InfType.find( ')' ) ]
                chaine = chaine +"output : "+ ss[2] + ", type :" +text + "\n"

        QMessageBox.information(None, "Node : "+e, chaine,
                        QMessageBox.Ok,
                        QMessageBox.Ok)

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
        # print (self.cmd.run("dg.entity.Entity.entities['"+s+"'].display()"))
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
            if "0" in self.filter:
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
            for j in self.filter:
                for i in self.filter:
                    if i == "0" or (i in f and j in t):
                        
                        if f not in self.SignalBlocked:
            	            edge = self.graph.addEdge (self.nodes[f], self.nodes[t])
                            # TODO set edge properties
                            edge.setAttribute("color", "red")
                            self.SignalBlocked = self.SignalBlocked + f + " "
        self._edgeEntitySignals (t)
        pass

    def _nodeEntity(self, e):
        for i in self.filter:
            if i == "0" or i in e:
                if e not in self.EntityBlocked:
                    self.nodes[e] = self.graph.addNode (e)
                    self.EntityBlocked = self.EntityBlocked + e + " "

    def _edgeEntitySignals(self, e):

        again = 0
        str_signals = self.cmd.run("[ s.name for s in dg.entity.Entity.entities['"+e+"'].signals() ]")
        signals = eval(str_signals)
        for s in signals:
            ss = s.split("::")
            if len(ss) != 3:
                print ("Cannot handle"+ s)
            elif ss[1].startswith("in"):
                plugged = self.cmd.run("dg.entity.Entity.entities['"+e+"'].signal('"+ss[-1]+"').isPlugged()")
                other_s = self.cmd.run("dg.entity.Entity.entities['"+e+"'].signal('"+ss[-1]+"').getPlugged().name if dg.entity.Entity.entities['"+e+"'].signal('"+ss[-1]+"').isPlugged() else None")
                if other_s is not None and s != other_s:
                    idx = other_s.index('(')+1
                    other_e = other_s[idx:other_s.index(')',idx)]
                    for i in self.filter:
                        for j in self.filter:
                            if i == "0" or (i in other_e and j in e and e != other_e):
                                if again != 0:
                                    pass
                                else:
                                    if not self.nodes.has_key(other_e):
                                        self._createGraphBackwardFromEntity(other_e)
                                    self.edges[s] = (e, self.graph.addEdge (self.nodes[other_e], self.nodes[e], ss[2]))
                                    self.edgesBack[self.edges[s][1]] = s                                     
                                again += 1
                elif ss[1].startswith("out"):
                    pass

            again = 0


    def _nodeContextMenu (self, node):
        e = node.getAttribute("label")
        if self.nodes.has_key(e):
            menu = QtGui.QMenu("Entity " + e, self.view)
            a = menu.addAction("Show graph backward")
            a.connect(Qt.SIGNAL("triggered()"), lambda: self.createGraphBackwardFromEntity(e))
            menu.popup(QtGui.QCursor.pos())
            b = menu.addAction("Show Node Info")
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
            print (edge)
