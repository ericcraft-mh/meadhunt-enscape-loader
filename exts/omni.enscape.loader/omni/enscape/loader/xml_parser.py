import xml.etree.ElementTree as ET
from numpy import complex128
import omni.kit
import omni.kit.commands
import omni.usd
from pxr import Gf, UsdGeom
import math
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
    def __init__(self, debug=False, xml=None, mode=0, scenepath="/World"):
        self._debug = debug
        self._xml = xml
        self._mode = mode
        self._scenepath = scenepath
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
        return float(self._root[0][self.keys_count()-1].attrib.get("timestampSeconds"))

    def time_key(self):
        return self.length_xml()/self.keys_count()
    
    def keys_count(self):
        return int(self._root[0].attrib.get("count"))

    def get_fov(self):
        fovList = []
        for index in range(0, self.keys_count()):
            if self._root[0][index].attrib.get("fieldOfViewRad") != None:
                fovList.append([float(self._root[0][index].attrib.get("fieldOfViewRad")),int(index)])
            # print("FOV: ",self._root[0][index].attrib.get("fieldOfViewRad"))
        # print(theList)
        return fovList

    def get_value(self, order:0, item:0, axis:str):
        return float(self._root[0][order][item].attrib.get(axis))

    def get_pos(self, index:0):
        pos = Gf.Vec3d((self.get_value(index,0,'x')*100),-(self.get_value(index,0,'z')*100),(self.get_value(index,0,'y')*100))
        return pos

    def get_xform(self, index:0):
        # Input vectors
        vecpos = Gf.Vec3d((self.get_value(index,0,'x')*100),-(self.get_value(index,0,'z')*100),(self.get_value(index,0,'y')*100))
        vecdir = Gf.Vec3d(-(self.get_value(index,1,'x')),(self.get_value(index,1,'z')),-(self.get_value(index,1,'y')))
        vecup = Gf.Vec3d(0,0,1)
        # Generate normalized rotation vector from direction vector
        xaxis = Gf.Cross(vecup, vecdir)
        xnorm = xaxis/Gf.Normalize(xaxis)
        yaxis = Gf.Cross(vecdir, xaxis)
        ynorm = yaxis/Gf.Normalize(yaxis)
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

    def get_focalLength(self, cam, fov):
        focalLength = (cam.GetAttribute("horizontalAperture").Get()/2)/math.tan(fov/2)
        return focalLength

    def parse_xml(self):
        stage = omni.usd.get_context().get_stage()
        self._keys_total = self.keys_count()
        self._is_valid = self.valid_xml()
        self._duration = self.length_xml()
        self._time_per_key = self.time_key()
        self._fov_list = self.get_fov()
        for index in range(0, self._keys_total):
            # Create Camera Path
            camera_path = f"{self._scenepath.get_value_as_string()}"+"/EnscapeCamera"+f"{index:02d}"
            # Create Camera prim
            camera_prim = stage.DefinePrim(camera_path, "Camera")
            camera_prim.GetAttribute("horizontalAperture").Set(23.760)
            camera_prim.GetAttribute("verticalAperture").Set(13.365)
            # Set focalLength from XML or set to 90 degrees
            if len(self._fov_list) == 1:
                camera_prim.GetAttribute("focalLength").Set(self.get_focalLength(camera_prim,self._fov_list[0][0]))
            else:
                camera_prim.GetAttribute("focalLength").Set(self.get_focalLength(camera_prim,math.radians(90.0)))
            # Check if xformOp:transform exists
            # Set or create xformOp:transform
            if camera_prim.HasAttribute("xformOp:transform"):
                transform = camera_prim.GetAttribute("xformOp:transform")
            else:
                xform = UsdGeom.Xformable(camera_prim)
                transform = xform.AddTransformOp()
            # Set the Camera transform matrix
            transform.Set(self.get_xform(index))
            # Debug
            if self._debug:
                print(f"Camera Path: {camera_path}")
        if self._debug:
            print(f"\n\n >>> Valid: {self._is_valid}\n >>> Keys Count: {self._keys_total}\n >>> Length: {self._duration}\n >>> TimePerKey: {self._time_per_key}\n")
        if self._is_valid:
            if self._mode == 0:
                print(f"Mode {self._mode}: WIP try again later")
            if self._mode == 1:
                print(f"Mode {self._mode}: WIP try again later")
            if self._mode == 2:
                print(f"Mode {self._mode}: WIP try again later")
            if self._mode == 3:
                print(f"Mode {self._mode}: WIP try again later")
            # print(f"{self._root.tag}")