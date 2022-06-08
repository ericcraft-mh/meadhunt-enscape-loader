import xml.etree.ElementTree as ET
import omni.kit.commands
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
    def __init__(self, debug=False, xml=None, mode=0):
        self._debug = debug
        self._xml = xml
        self._mode = mode
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

    def create_cam(self):
        omni.kit.commands.execute('CreatePrimWithDefaultXform', prim_type='Camera', attributes={'focusDistance': 400, 'focalLength': 24})

    def parse_xml(self):
        self._keys_total = self.keys_count()
        self._is_valid = self.valid_xml()
        self._duration = self.length_xml()
        self._time_per_key = self.time_key()
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
            print(f"{self._root.tag}")