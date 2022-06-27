import xml.etree.ElementTree as ET
from numpy import arctan2, complex128, deg2rad
import numpy
import omni.kit
import omni.kit.commands
from omni.kit.menu.utils import scripts
import omni.usd
from pxr import Gf, UsdGeom
import math
import omni.anim.curve.scripts as anim
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
    def __init__(self, debug=False, xml=None, mode=0, scenepath="/World", cameraname="EnscapeCamera"):
        self._debug = debug
        self._xml = xml
        self._mode = mode
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

    def length_xml(self):
        try:
            outval = float(self._root[0][self.keys_count()-1].attrib.get("timestampSeconds"))
        except:
            outval = float(0)
        return outval

    def time_key(self):
        return self.length_xml()/self.keys_count()
    
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

    def get_pos(self, index=0):
        thePos = 100*Gf.Vec3d(self.get_value(index,0,'x'),-self.get_value(index,0,'z'),self.get_value(index,0,'y'))
        return thePos

    def get_dir(self, index=0):
        theDir = Gf.Vec3d(-(self.get_value(index,1,'x')),(self.get_value(index,1,'z')),-(self.get_value(index,1,'y')))
        return theDir

    def _xform(self, index=0):
        # Input vectors
        vecpos = self.get_pos(index)
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

    def _quat2euler(self, q:Gf.Quatd):
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
            None
        else:
            xform = UsdGeom.Xformable(camera_prim)
            # transform = xform.AddTransformOp()
            xposition = xform.AddTranslateOp()            
            xrotation = xform.AddRotateXYZOp()
            xscale = xform.AddScaleOp()
        # Set the Camera transform matrix

        xposition.Set(self._xform(index).ExtractTranslation())
        xrotation.Set(self._quat2euler(self._xform(index).ExtractRotationQuat()))
        xscale.Set(Gf.Vec3d(1,1,1))

        # transform.Set(self.get_xform(index))
        # Debug
        if self._debug:
            print(f"Camera Path: {camera_path}")
        return camera_prim

    def parse_xml(self):
        self._is_valid = self.valid_xml()
        self._keys_total = self.keys_count()
        if self._debug:
            print(f"\n\n >>> Valid: {self._is_valid}\n >>> Keys Count: {self._keys_total}\n >>> Length: {self.length_xml()}\n >>> TimePerKey: {self.time_key()}\n")
        if self._is_valid:
            if self._mode == 0:
                print(f"Mode {self._mode}: WIP try again later")
            if self._mode == 1:
                print(f"Mode {self._mode}: WIP try again later")
            if self._mode == 2:
                print(f"Mode {self._mode}: Ready for Testing")
                for index in range(0, self._keys_total):
                    newcam =self.create_cameras(index)
                    newcam.GetAttribute("focalLength").Set(self.get_focalLength(camerasList[index],math.radians(90.0)))
                    if newcam.HasAttribute("xformOp:translate"):
                        anim.AddAnimCurves(paths=[f"{newcam}.xformOp:translate"],)
            if self._mode == 3:
                print(f"Mode {self._mode}: Ready for Testing")
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