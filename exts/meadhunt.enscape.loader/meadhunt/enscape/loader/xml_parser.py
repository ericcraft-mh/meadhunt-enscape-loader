import xml.etree.ElementTree as ET

from numpy import arctan2
import numpy
import math
import asyncio

import omni.kit
import omni.kit.commands
import omni.kit.app
import omni.usd
import omni.timeline

from pxr import Gf, UsdGeom
from pxr.Usd import TimeCode

## Sample Structure:
# <?xml version="1.0" ?>
# <VideoPath version="1" easingInOut="1" shakyCam="0">
#     <Keyframes count="18">
#         <Keyframe order="0" timestampSeconds="0.0">
#             <Position x="372.363" y="11.3997" z="71.0269" />
#             <LookAt x="-0.362576" y="-0.161124" z="0.91792" />
#         </Keyframe>
#     </Keyframes>
# </VideoPath>

## Sample Access:
# root: VideoPath
# root[0]: Keyframes
# root[0][#] Keyframe
# root[0][#][0]: Position
# root[0][#][1]: LookAt

## Sample Values:
# Total Number of Keys: int(root[0].attrib.get("count"))
# KeyFrame Number: int(root[0][0].attrib.get("order"))
# Keyframe Time in Seconds: float(root[0][0].attrib.get("timestampSeconds"))
# Position X Value: float(root[0][0][0].attrib.get("x"))
# LookAt X Value: float(root[0][0][1].attrib.get("x"))
# Total Duration: float(root[0][int(root[0].attrib.get("count"))-1].attrib.get("timestampSeconds"))
# Seconds per Key: float(root[0][int(root[0].attrib.get("count"))-1].attrib.get("timestampSeconds"))/int(root[0].attrib.get("count"))

class xml_data:
    def __init__(self, debug=False, xml=None, items=[0,0,0], scenepath="/World", cameraname="EnscapeCamera"):
        self._debug = debug
        self._xml = xml
        self._mode = items[0]
        self._method = items[1]
        self._fit = items[2]
        self._scenepath = scenepath
        self._cameraname = cameraname
        tree = ET.parse(self._xml)
        self._root = tree.getroot()

    def valid_xml(self) -> bool:
        self._is_valid = False
        if self._root.tag == 'VideoPath':
            if self._debug:
                print(f"{self._xml}: is an Enscape XML")
            self._is_valid = True
            return True
        else:
            if self._debug:
                print(f"{self._xml}: is NOT an Enscape XML")
            return False

    def total_time(self):
        try:
            outval = float(self._root[0][self.keys_count()-1].attrib.get("timestampSeconds"))
        except:
            outval = float(0)
        return outval

    def time_key(self):
        return self.total_time()/self.keys_count()
    
    def keys_count(self):
        return int(self._root[0].attrib.get("count"))

    def get_fov(self, index=0):
        try:
            fovOut = float(self._root[0][index].attrib.get("fieldOfViewRad"))
        except:
            fovOut = math.radians(90.0)
        return fovOut

    def get_value(self, order=0, item=0, axis=str):
        try:
            outval = float(self._root[0][order][item].attrib.get(axis))
        except:
            outval = float(0)
        return outval

    def get_keyTime(self, index=0):
        theKey = self._root[0][index].attrib.get("timestampSeconds")
        if theKey == None:
            theKey = self.time_key()*index       
        theTime = float(theKey)
        theTime = round(theTime)
        return theTime

    def get_pos(self, index=0):
        thePos = 100*Gf.Vec3d(self.get_value(index,0,'x'),-self.get_value(index,0,'z'),self.get_value(index,0,'y'))
        return thePos

    def get_dir(self, index=0):
        theDir = Gf.Vec3d(-(self.get_value(index,1,'x')),(self.get_value(index,1,'z')),-(self.get_value(index,1,'y')))
        return theDir

    def get_rot(self, index=0):
        theRot = self._quat2euler(self._xform(index))
        return theRot

    def _closestRot(self, index=0):
        theRot = self.get_rot(index)
        nextRot = self.get_rot(index+1)
        vec360 = Gf.Vec3d(0,0,360)
        if numpy.linalg.norm(theRot-nextRot) > numpy.linalg.norm((theRot+vec360)-nextRot):
            theRot += vec360
        return theRot

    def _xform(self, index=0):
        # Input vectors
        vecpos = Gf.Vec3d(0,0,0)
        vecdir = self.get_dir(index)
        vecup = Gf.Vec3d(0,0,1)
        # Generate normalized rotation vector from direction vector
        xaxis = Gf.Cross(vecup, vecdir)
        xnorm = Gf.GetNormalized(xaxis)
        yaxis = Gf.Cross(vecdir, xaxis)
        ynorm = Gf.GetNormalized(yaxis)
        if Gf.GetLength(xnorm) == 0.0:
            xnorm = Gf.Vec3d(1,0,0)
        if Gf.GetLength(ynorm) == 0.0:
            ynorm = Gf.Vec3d(0,1,0)
        if Gf.GetLength(vecdir) == 0.0:
            vecdir = Gf.Vec3d(0,0,1)
        # Build transformation matrix
        column0 = Gf.Vec4d(xnorm[0], ynorm[0], vecdir[0], vecpos[0])
        column1 = Gf.Vec4d(xnorm[1], ynorm[1], vecdir[1], vecpos[1])
        column2 = Gf.Vec4d(xnorm[2], ynorm[2], vecdir[2], vecpos[2])
        column3 = Gf.Vec4d(0,0,0,1)
        # Set transformation matrix
        xformmat = Gf.Matrix4d()
        xformmat.SetColumn(0, column0)
        xformmat.SetColumn(1, column1)
        xformmat.SetColumn(2, column2)
        xformmat.SetColumn(3, column3)
        return xformmat

    def _quat2euler(self, xform:Gf.Matrix4d):
        q = xform.ExtractRotationQuat()
        qw = q.GetReal()
        qx = q.GetImaginary()[0]
        qy = q.GetImaginary()[1]
        qz = q.GetImaginary()[2]

        sinr_cosp = 2*(qw*qx+qy*qz)
        cosr_cosp = 1-2*(qx*qx+qy*qy)
        xaxis = arctan2(sinr_cosp,cosr_cosp)
        sinp = 2*(qw*qy-qz*qx)
        if Gf.Abs(sinp) >= 1:
            yaxis = math.copysign(math.pi/2,sinp)
        else:
            yaxis = math.asin(sinp)
        siny_cosp = 2*(qw*qz+qx*qy)
        cosy_cosp = 1-2*(qy*qy+qz*qz)
        zaxis = math.atan2(siny_cosp,cosy_cosp)
        euler = Gf.Vec3d(Gf.RadiansToDegrees(xaxis),Gf.RadiansToDegrees(yaxis),Gf.RadiansToDegrees(zaxis))
        return euler

    def _focalLength(self, cam=None, fov=math.radians(90.0)):
        if cam != None:
            focalLength = (cam.GetAttribute("horizontalAperture").Get()/2)/math.tan(fov/2)
            return focalLength

    def create_cameras(self, index=0):
        stage = omni.usd.get_context().get_stage()
        self._fov = self.get_fov(index)
        # Create Camera Path
        camera_path = f"{self._scenepath}"+"/"+f"{self._cameraname}{index:0{len(str(self.keys_count()))}d}"
        # Create Camera prim
        camera_prim = stage.DefinePrim(camera_path, "Camera")    
        camera_prim.GetAttribute("horizontalAperture").Set(23.760)
        camera_prim.GetAttribute("verticalAperture").Set(13.365)
        # Set focalLength from XML or set to 90 degrees
        camera_prim.GetAttribute("focalLength").Set(self._focalLength(camera_prim,self._fov))
        # Check if xformOp:transform exists
        # Set or create xformOp:transform
        if camera_prim.HasAttribute("xformOp:translate"):
            xposition = camera_prim.GetAttribute("xformOp:translate")
            xrotation = camera_prim.GetAttribute("xformOp:rotateXYZ")
            xscale = camera_prim.GetAttribute("xformOp:scale")
        else:
            xform = UsdGeom.Xformable(camera_prim)
            # transform = xform.AddTransformOp()
            xposition = xform.AddTranslateOp()
            xrotation = xform.AddRotateXYZOp()
            xscale = xform.AddScaleOp()
        # Set the Camera transform matrix
        xform = UsdGeom.Xformable(camera_prim)
        # transform = xform.AddTransformOp()
        # xposition = xform.AddTranslateOp()            
        # xrotation = xform.AddRotateXYZOp()
        # xscale = xform.AddScaleOp()
        xposition.Set(self.get_pos())
        xrotation.Set(self.get_rot())
        xscale.Set(Gf.Vec3d(1,1,1))
        # transform.Set(self.get_xform(index))
        # Debug
        if self._debug:
            print(f"Camera Path: {camera_path}")
        return camera_prim

    def parse_xml(self):
        self._is_valid = self.valid_xml()
        self._keys_total = self.keys_count()
        if self._fit == 0:
            timeinterface = omni.timeline.get_timeline_interface()
            timefps = timeinterface.get_time_codes_per_seconds()
            totaltime = round(self.total_time()*timefps)
            totaltime /= timefps
            timeinterface.set_end_time(totaltime)
        if self._debug:
            print(f"\n\n >>> Valid: {self._is_valid}\n >>> Keys Count: {self._keys_total}\n >>> Length: {self.total_time()}\n >>> TimePerKey: {self.time_key()}\n")
        if self._is_valid:
            stage = omni.usd.get_context().get_stage()
            if UsdGeom.GetStageUpAxis(stage) != 'Z':
                UsdGeom.SetStageUpAxis(stage, 'Z')
            if self._method == 0:
                print(f"Method {self._method}: WIP try again later")
            if self._method == 1:
                print(f"Method {self._method}: Ready for Testing")
                newcam = self.create_cameras()
                newcampath = newcam.GetPrimPath()
                newcam.GetAttribute("focalLength").Set(self._focalLength(newcam,math.radians(90.0)))
                if newcam.HasAttribute("xformOp:translate"):
                    tpath = f"{newcampath}.xformOp:translate"
                    rpath = f"{newcampath}.xformOp:rotateXYZ"
                    # omni.kit.commands.execute("AddAnimCurves",paths=[tpath,rpath])
                    for index in range(0, self._keys_total):
                        # Set Anim Curve Keys for translate
                        omni.kit.commands.execute("SetAnimCurveKey",paths=[tpath],time=TimeCode(self.get_keyTime(index)*timefps),value=self.get_pos(index),inTangentType="Linear",outTangentType="Linear")
                        # Set Anim Curve Keys for rotateXYZ
                        omni.kit.commands.execute("SetAnimCurveKey",paths=[rpath],time=TimeCode(self.get_keyTime(index)*timefps),value=self._closestRot(index),inTangentType="Linear",outTangentType="Linear")
            if self._method == 2:
                print(f"Method {self._method}: Ready for Testing")
                for index in range(0, self._keys_total-1):
                    newcam = self.create_cameras(index)
                    newcampath = newcam.GetPrimPath()
                    newcam.GetAttribute("focalLength").Set(self._focalLength(newcam,math.radians(90.0)))
                    if newcam.HasAttribute("xformOp:translate"):
                        tpath = f"{newcampath}.xformOp:translate"
                        rpath = f"{newcampath}.xformOp:rotateXYZ"
                        # Set Anim Curve Keys for translate
                        omni.kit.commands.execute("SetAnimCurveKey",paths=[tpath],time=TimeCode(self.get_keyTime(index)*timefps),value=self.get_pos(index))
                        omni.kit.commands.execute("SetAnimCurveKey",paths=[tpath],time=TimeCode(self.get_keyTime(index+1)*timefps),value=self.get_pos(index+1))                        
                        # Set Anim Curve Keys for rotateXYZ
                        omni.kit.commands.execute("SetAnimCurveKey",paths=[rpath],time=TimeCode(self.get_keyTime(index)*timefps),value=self._closestRot(index))
                        omni.kit.commands.execute("SetAnimCurveKey",paths=[rpath],time=TimeCode(self.get_keyTime(index+1)*timefps),value=self._closestRot(index+1))
            if self._method == 3:
                print(f"Method {self._method}: Ready for Testing")
                camerasList = []
                fovList = []
                for index in range(0, self._keys_total):
                    camerasList.append(self.create_cameras(index))
                    try:
                        fovOut = self._root[0][index].attrib.get("fieldOfViewRad")
                    except:
                        fovOut = None
                    if fovOut:
                        fovList.append(self.get_fov(index))
                for index in range(0, self._keys_total):
                    if len(fovList) == 1:
                        camerasList[index].GetAttribute("focalLength").Set(self.get_focalLength(camerasList[index],fovList[0]))
                    if len(fovList) == 0:
                        camerasList[index].GetAttribute("focalLength").Set(self.get_focalLength(camerasList[index],math.radians(90.0)))
                # print(camerasList)
            # print(f"{self._root.tag}")