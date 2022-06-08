import xml.etree.ElementTree as ET

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
        self._key_count = 0
        self._root = None
        self._is_vaild = False
        self._mode = mode

    def valid_xml(self) -> bool:
        self._is_valid = False
        tree = ET.parse(self._xml)
        self._root = tree.getroot()
        if self._root.tag == 'VideoPath':
            if self._debug:
                print(f"{self._xml}: is an Enscape XML")
            self._is_valid = True
            return True
        else:
            if self._debug:
                print(f"{self._xml}: is NOT an Enscape XML")
            return False

    def parse_xml(self):
        self._is_valid = self.valid_xml()
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