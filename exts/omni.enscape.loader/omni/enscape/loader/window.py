import omni.kit.ui
from omni.kit.window.popup_dialog import style
import omni.ui as ui
import os

from omni.kit.window.filepicker.dialog import FilePickerDialog
from .xml_parser import xml_data
from omni.ui import color as cl

class ExtensionWindow(ui.Window):
    LABEL_WIDTH = 80
    SPACER_WIDTH = 5
    BUTTON_SIZE = 24
    METHOD_LIST = ["Continous: Smooth","Continuous: Linear","Multiple: Linear","Multiple: Static"]
    COMBO_MODE = None
    btn_click = ui.Button

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

    def destroy(self):
        if self._open_file_dialog:
            self._open_file_dialog.destroy()
            self._open_file_dialog = None

    def show(self):
        self.visible = True
        self.focus()

    def hide(self):
        self.visible = False

    def _build_ui(self):
        with self.frame:
            with ui.VStack(height=0):
                with ui.VStack(spacing=5, name="frame_v_stack"):
                    ui.Spacer(height=0)
                    self._create_path("XML Path:", "")
                    ui.Spacer(height=0)
                    self.COMBO_MODE = self._create_combo("Method:", self.METHOD_LIST)
                    ui.Spacer(height=0)
                self.btn_click = ui.Button("Click Me", name="BtnClick", clicked_fn=lambda: self._on_click(), style={"color": cl.shade("aqua", transparent=0x20FFFFFF, white=0xFFFFFFFF)})
                self.btn_click.enabled = False
                ui.set_shade("transparent")

    def _on_filter_xml(self, item) -> bool:
        """Callback to filter the choices of file names in the open or save dialog"""
        if self.DEBUG:
            print(f"current_filter_option: {self._open_file_dialog.current_filter_option}")
        if not item or item.is_folder:
            return True
        if self._open_file_dialog.current_filter_option == 0:
            # Show only files with listed extensions
            # print("XML Filter")
            return item.path.endswith(".xml")
        else:
            # Show All Files (*)
            # print("All Filter")
            return True

    def _create_path(self, str, paths):
        with ui.HStack(style={"Button":{"margin":0.0}}):
            ui.Label(str, name="label", width=self.LABEL_WIDTH)
            self._str_field = ui.StringField(name="xmlpath", height=self.BUTTON_SIZE).model
            self._str_field.set_value(paths)
            ui.Spacer(width=(self.SPACER_WIDTH/2))
            ui.Button(image_url="resources/icons/folder.png", width=self.BUTTON_SIZE, height=self.BUTTON_SIZE, clicked_fn=lambda: self._xml_file(self._str_field))
            # ui.Spacer(width=self.SPACER_WIDTH)
            # ui.Button(image_url="resources/icons/find.png", width=self.BUTTON_SIZE, height=self.BUTTON_SIZE)

    def _create_combo(self, str, items):
        with ui.HStack():
            ui.Label(str, name="label", width=self.LABEL_WIDTH)
            combo = ui.ComboBox(0)
            for item in items:
                combo.model.append_child_item(None, ui.SimpleStringModel(item))
        return combo
 
    def _on_click(self):
        selected_item = self.COMBO_MODE.model.get_item_value_model().as_int
        if self._valid_xml:
            xml_data(self.DEBUG, self._file_return, selected_item).parse_xml()
        else:
            print("Please select a valid Enscape XML File!")
        if self.DEBUG:
            print(f"Selected Item: {selected_item} | {self.METHOD_LIST[selected_item]}")

    def _xml_file(self, field):
        def _on_click_open(file_name: str, directory_path: str):
            """Callback executed when the user selects a file in the open file dialog"""
            if file_name != "" and directory_path != None:
                self._file_return = os.path.join(directory_path, file_name)
                self._valid_xml = xml_data(self.DEBUG, self._file_return).valid_xml()

            if self._file_return and self._valid_xml:
                field.set_value(self._file_return)
                if self._open_file_dialog:
                    self._open_file_dialog.hide()

        def _on_click_cancel(file_name: str, directory_path: str):
            field.set_value("None")
            if self._open_file_dialog:
                self._open_file_dialog.hide()

        if self._open_file_dialog:
            self._open_file_dialog.hide()
            self._open_file_dialog.destroy()

        # self._open_file_dialog = FilePickerDialog(
        #         "Select XML File",
        #         apply_button_label="Select",
        #         click_apply_handler=lambda f, d: _on_click_open(f, d),
        #         click_cancel_handler=lambda f, d: _on_click_cancel(f, d),
        #         file_extension_options = [("*.xml", "Files (*.xml)")],
        #         item_filter_fn=lambda item: self._on_filter_xml(item)
        #     )
        self._open_file_dialog = FilePickerDialog(
                "Open XML File",
                apply_button_label="Open",
                click_apply_handler=lambda f, d: _on_click_open(f, d),
                click_cancel_handler=lambda f, d: _on_click_cancel(f, d),
                item_filter_options= ["XML Files (*.xml)", "All Files (*.*)"],
                item_filter_fn=lambda item: self._on_filter_xml(item)
            )
        self._open_file_dialog.show()

        if self._file_return:
            self.btn_click.enabled = not self.btn_click.enabled
            ui.set_shade("white")
            field.set_value(self._file_return)

    def _on_visibility_changed(self, visible):
        if not visible:
            omni.kit.ui.get_editor_menu().set_value(self._menu_path, False)