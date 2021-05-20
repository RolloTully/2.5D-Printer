from direct.showbase.ShowBase import ShowBase
from direct.showbase import DirectObject
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3, DirectionalLight,  GeoMipTerrain
from pandac.PandaModules import WindowProperties
import cv2, sys, math
import numpy as np
from random import randint


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        '''Disabling standard mouse movments'''
        self.disableMouse()
        self.props = WindowProperties()
        self.props.setCursorHidden(True)
        self.props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(self.props)
        self.MouseWatch = self.mouseWatcherNode

        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.Player_Pos = np.array([1,1]) #starts within bounds of map
        self.Player_Hp = [0,0]
        self.Z_Scale = 60

        '''Add new light to scene'''
        self.dlight = DirectionalLight('my dlight')
        self.dlnp = render.attachNewNode(self.dlight)
        self.dlnp.setHpr(0, -45, 0)
        self.render.setLight(self.dlnp)

        '''Build terrain from height map'''
        self.terrain = GeoMipTerrain("")
        self.terrain.setHeightfield("pen.png")
        self.terrain.setColorMap("pen.png")
        self.terrain.setBlockSize(32)
        self.terrain.setNear(100)
        self.terrain.setFar(400)
        self.terrain.setFocalPoint(self.camera)
        self.root = self.terrain.getRoot()
        self.root.reparentTo(render)
        self.root.setSz(self.Z_Scale)
        self.terrain.generate()

        '''Adding tasks to task manager'''
        self.taskMgr.add(self.UpdatePlayerTask, "UpdatePlayerTask")
        self.taskMgr.add(self.UpdateCameraTask, "UpdateCameraTask")
        self.taskMgr.add(self.UpdateTerrainTask, "UpdateTerrainTask")

    def UpdateTerrainTask(self,task):
        self.terrain.update()
        return task.cont

    def UpdatePlayerTask(self,task):
        self.accept('keystroke', self.Change_Pos_and_Hp)
        self.elevation = self.terrain.getElevation(self.Player_Pos[0],self.Player_Pos[1])*self.Z_Scale
        self.camera.setPos(self.Player_Pos[0],self.Player_Pos[1], self.elevation+3)
        return task.cont

    def Change_Pos_and_Hp(self, keyname):
        self.Playerangle = np.radians(self.Player_Hp[0])
        if keyname == "w":
            self.Player_Pos = self.Player_Pos + np.array([-np.sin(self.Playerangle),np.cos(self.Playerangle)])
        elif keyname == "a":
            self.Player_Pos = self.Player_Pos + np.array([-np.cos(self.Playerangle),np.sin(self.Playerangle)])
        elif keyname == "s":
            self.Player_Pos = self.Player_Pos + np.array([np.sin(self.Playerangle),-np.cos(self.Playerangle)])
        elif keyname == "d":
            self.Player_Pos = self.Player_Pos + np.array([np.cos(self.Playerangle),-np.sin(self.Playerangle)])
        else:
            print(keyname)
            pass

    def UpdateCameraTask(self, task):
        if self.MouseWatch.hasMouse():
            self.x, self.y = self.MouseWatch.getMouseX()*10, self.MouseWatch.getMouseY()*10
            self.props = self.win.getProperties()
            self.win.movePointer(0, self.props.getXSize() // 2, self.props.getYSize() // 2)
            self.Player_Hp[0]-=self.x
            self.Player_Hp[1]+=self.y
        self.camera.setHpr(self.Player_Hp[0],self.Player_Hp[1],0)
        return Task.cont


app = MyApp()
app.run()
