
from aisikl.exceptions import AISParseError


# TODO: Document Component and all subclasses.

class Component:
    def __init__(self, dialog_soup, element, dialog):
        self.dialog = dialog
        self.id = element['id']
        self.jsct = element['jsct']
        self.used_listeners_mask = int(element.get('usedlistenersmask', '0'))
        self.enabled = element.get('enabled', 'true') == 'true'
        self.enabled_in_ui = element.get('enabledinui', 'true') == 'true'
        self.visible = element.get('visible', 'true') == 'true'
        self.visible_in_ui = element.get('visibleinui', 'true') == 'true'
        self.title = element.get('_title')
        self.popup_menu = element.get('popupmenu')

        if int(element.get('state', '1')) == 2:
            raise AISParseError('STATE_DT is not supported')

        parent = element.find_parent(jsct=True)
        self.parent_id = parent['id'] if parent else None

    def log(self, *args, **kwargs):
        self.dialog.app.ctx.log(*args, **kwargs)

    @property
    def parent(self):
        return self.dialog.components[self.parent_id]

    def is_really_enabled(self):
        return self.enabled and self.enabled_in_ui

    def _ais_setState(self, value):
        if int(value) == 2: raise AISParseError('STATE_DT is not supported')
    def _ais_setUsedListenersMask(self, value):
        self.used_listeners_mask = int(value)
    def _ais_setEnabled(self, value):
        self.enabled = (value == 'true')
    def _ais_setEnabledInUI(self, value):
        self.enabled_in_ui = (value == 'true')
    def _ais_setVisible(self, value):
        self.visible = (value == 'true')
    def _ais_setVisibleInUI(self, value):
        self.visible_in_ui = (value == 'true')
    def _ais_setTitle(self, value):
        self.title = value
    def _ais_setPopupMenu(self, value):
        self.popup_menu = value
    def _ais_setForeground(self, value):
        pass
    def _ais_setBackground(self, value):
        pass
