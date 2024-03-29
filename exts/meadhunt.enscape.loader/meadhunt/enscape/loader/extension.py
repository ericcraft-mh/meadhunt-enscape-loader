import omni.ext
import omni.ui as ui
import omni.kit.ui

from .window import ExtensionWindow

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.

class EnscapeIO(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.

    # Class Variables
    DEBUG = True
    WINDOW_TITLE = "Enscape Camera Loader"

    def __init__(self):
        pass

    def on_startup(self, ext_id):
        print("[meadhunt.enscape.loader] Enscape Camera Loader startup")

        # Note the "Window" part of the path that directs the new menu item to the "Window" menu.
        self._menu_path = f"Window/Mead & Hunt/{self.WINDOW_TITLE}"
        if self.DEBUG:
            print(f"{self._menu_path}")
        
        # Menu setup and window initialization
        self._window = None
        self._menu = omni.kit.ui.get_editor_menu().add_item(self._menu_path, self._on_menu_click, True)
        omni.kit.ui.get_editor_menu().set_value(self._menu_path, False)

    def on_shutdown(self):
        print("[meadhunt.enscape.loader] Enscape Camera Loader shutdown")

        if self._window:
            self._window.hide()
            self._window.destroy()
            self._window = None   

        omni.kit.ui.get_editor_menu().remove_item(self._menu)

    def _on_menu_click(self, menu, toggled):
        """Handles showing and hiding the window from the 'Windows' menu."""
        if toggled:
            if self._window is None:
                self._window = ExtensionWindow(self.WINDOW_TITLE, 300, 300, menu, self.DEBUG)
            else:
                self._window.show()
        else:
            if self._window:
                self._window.hide()
                self._window.destroy()

    def destroy(self):
        if self._window:
            self._window.hide()
            self._window = None

