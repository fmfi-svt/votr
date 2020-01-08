
from aisikl.exceptions import AISParseError


def is_true(value):
    return value == 'true' or value == True


# TODO: Document Component and all subclasses.

class Component:
    def __init__(self, dialog, id, type, parent_id, properties, element):
        self.dialog = dialog
        self.id = id
        self.component_type = type
        self.used_listeners_mask = properties.get('ulm', 0)
        self.enabled = properties.get('e', True)
        self.enabled_in_ui = properties.get('enabledInUI', True)
        self.visible = properties.get('v', True)
        self.visible_in_ui = properties.get('visibleInUI', True)
        self.title = properties.get('title')
        self.popup_menu = properties.get('pm')

        if properties.get('state', 1) == 2:
            raise AISParseError('STATE_DT is not supported')

    def log(self, *args, **kwargs):
        self.dialog.app.ctx.log(*args, **kwargs)

    def is_really_enabled(self):
        return self.enabled and self.enabled_in_ui

    def _ais_setState(self, value):
        if int(value) == 2: raise AISParseError('STATE_DT is not supported')
    def _ais_setUsedListenersMask(self, value):
        self.used_listeners_mask = int(value)
    def _ais_setEnabled(self, value):
        self.enabled = is_true(value)
    def _ais_setEnabledInUI(self, value):
        self.enabled_in_ui = is_true(value)
    def _ais_setVisible(self, value):
        self.visible = is_true(value)
    def _ais_setVisibleInUI(self, value):
        self.visible_in_ui = is_true(value)
    def _ais_setTitle(self, value):
        self.title = value
    def _ais_setPopupMenu(self, value):
        self.popup_menu = value
