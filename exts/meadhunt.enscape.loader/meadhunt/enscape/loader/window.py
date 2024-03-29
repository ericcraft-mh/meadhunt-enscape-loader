from ctypes import alignment
import omni.kit.ui
import omni.ui as ui
import os
import re

from omni.kit.window.filepicker.dialog import FilePickerDialog
from .xml_parser import xml_data
from omni.ui import color as cl

class ExtensionWindow(ui.Window):
    
    # Class Variables
    LABEL_WIDTH = 80
    SPACER_WIDTH = 5
    BUTTON_SIZE = 24
    MODE_LIST = ["Import", "Export"]
    METHOD_LIST = ["Continous: Smooth","Continuous: Linear","Multiple: Linear","Multiple: Static"]
    FIT_LIST = ["Match XML","Grow to Fit","Shrink to Fit"]
    COMBO_MODE = None    
    COMBO_METHOD = None

    def __init__(self, title, win_width, win_height, menu_path, debug_global):
        super().__init__(title, width=win_width, height=win_height)
        self._menu_path = menu_path
        self.DEBUG = debug_global
        self._file_return = None
        self._valid_xml = False
        self._open_file_dialog = None
        self.set_visibility_changed_fn(self._on_visibility_changed)
        self._build_ui()

    def on_shutdown(self):
        if self._open_file_dialog:
            self._open_file_dialog.destroy()
            self._open_file_dialog = None
        if self:
            self.destroy()
            self = None

    def destroy(self):
        if self._open_file_dialog:
            self._open_file_dialog = None
        if self:
            self = None

    def show(self):
        self.visible = True
        self.focus()

    def hide(self):
        self.visible = False

    def _build_ui(self):
        with self.frame:
            with ui.VStack(height=0):
                with ui.VStack(spacing=5, name="frame_v_stack"):

                    self._create_path("XML Path:", "")

                    with ui.HStack():
                        ui.Label("Scene Path:", name="scenelabel", width=self.LABEL_WIDTH)
                        self._scene_path = ui.StringField(name="scenepath", height=self.BUTTON_SIZE).model
                        self._scene_path.set_value("/World/Cameras")
                    with ui.HStack():
                        ui.Label("Name:", name="namelabel", width=self.LABEL_WIDTH)
                        self._camera_name = ui.StringField(name="namefield", height=self.BUTTON_SIZE).model
                        self._camera_name.set_value("EnscapeCamera")

                    self.COMBO_MODE = self._create_combo("Mode:", self.MODE_LIST, 0)
                    self.COMBO_MODE.enabled = False

                    self.COMBO_METHOD = self._create_combo("Method:", self.METHOD_LIST, 3)
                    self.COMBO_METHOD.enabled = True

                    self.COMBO_FIT = self._create_combo("Timeline:", self.FIT_LIST, 0)
                    self.COMBO_FIT.enabled = True
                self.btn_click = ui.Button("Click Me", name="BtnClick", clicked_fn=lambda: self._on_click(), style={"color": cl.shade("aqua", transparent=0x20FFFFFF, white=0xFFFFFFFF)}, enabled=False)
                ui.set_shade("transparent")

    def _on_filter_xml(self, item) -> bool:
        """Callback to filter the choices of file names in the open or save dialog"""
        if not item or item.is_folder:
            return True
        if self._open_file_dialog.current_filter_option == 0:
            # Show only files with listed extensions
            return item.path.endswith(".xml")
        else:
            # Show All Files (*)
            return True

    def _create_path(self, str, paths):
        with ui.HStack(style={"Button":{"margin":0.0}}):
            ui.Label(str, name="label", width=self.LABEL_WIDTH)
            self._str_field = ui.StringField(name="xmlpath", height=self.BUTTON_SIZE).model
            self._str_field.set_value(paths)
            ui.Spacer(width=(self.SPACER_WIDTH/2))
            ui.Button(image_url="resources/icons/folder.png", width=self.BUTTON_SIZE, height=self.BUTTON_SIZE, clicked_fn=lambda: self._xml_file(self._str_field))

    def _create_combo(self, str, items, selected):
        with ui.HStack():
            ui.Label(str, name="label", width=self.LABEL_WIDTH)
            combo = ui.ComboBox(selected)
            for item in items:
                combo.model.append_child_item(None, ui.SimpleStringModel(item))
        return combo
 
    def _on_click(self):
        mode_item = self.COMBO_MODE.model.get_item_value_model().as_int
        method_item = self.COMBO_METHOD.model.get_item_value_model().as_int
        fit_item = self.COMBO_FIT.model.get_item_value_model().as_int
        if self._valid_xml:
            xml_data(self.DEBUG, self._file_return, [mode_item,method_item,fit_item], self._scene_path.get_value_as_string(), self._camera_name.get_value_as_string()).parse_xml()
        else:
            print("Please select a valid Enscape XML File!")
        if self.DEBUG:
            print(f"Selected Item: {method_item} | {self.METHOD_LIST[method_item]}")
    
    def _fix_path(self, str):
        txt = re.split(r'[/\\]',str)
        return '/'.join(txt)

    def _xml_file(self, field):
        def _on_click_open(file_name: str, directory_path: str):
            """Callback executed when the user selects a file in the open file dialog"""
            if file_name != "" and directory_path != None:
                self._file_return = os.path.join(directory_path, file_name)
                self._file_return = self._fix_path(self._file_return)
                self._valid_xml = xml_data(self.DEBUG, self._file_return).valid_xml()

            if self._file_return and self._valid_xml:
                field.set_value(self._file_return)
                if self._open_file_dialog:
                    self._open_file_dialog.hide()

            if os.path.exists(self._file_return):
                self.btn_click.enabled = True
                ui.set_shade("white")
            else:
                self.btn_click.enabled = False
                ui.set_shade("transparent")

        def _on_click_cancel(file_name: str, directory_path: str):
            field.set_value("")
            self.btn_click.enabled = False
            ui.set_shade("transparent")
            if self._open_file_dialog:
                self._open_file_dialog.hide()

        if self._open_file_dialog:
            self._open_file_dialog.hide()
            self._open_file_dialog.destroy()

        self._open_file_dialog = FilePickerDialog(
                "Open XML File",
                apply_button_label="Open",
                click_apply_handler=lambda f, d: _on_click_open(f, d),
                click_cancel_handler=lambda f, d: _on_click_cancel(f, d),
                item_filter_options= ["XML Files (*.xml)", "All Files (*.*)"],
                item_filter_fn=lambda item: self._on_filter_xml(item)
            )
        self._open_file_dialog.show()

    def _on_visibility_changed(self, visible):
        if not visible:
            omni.kit.ui.get_editor_menu().set_value(self._menu_path, False)