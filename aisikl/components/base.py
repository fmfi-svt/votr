
from aisikl.exceptions import AISParseError


# TODO: Document everything.

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
        self.popup_menu = element.get('popup_menu')

        if element.get('state', '1') != '1':
            raise AISParseError('STATE_DT is not supported')
        self.state = 1

        parent = element.find_parent(jsct=True)
        self.parent_id = parent['id'] if parent else None

    @property
    def parent(self):
        return self.dialog.components[self.parent_id]

    def is_really_enabled(self):
        return self.enabled and self.enabled_in_ui

    def _ais_setState(self, value):
        if value != '1': raise AISParseError('STATE_DT is not supported')
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


class Control(Component):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.read_only = element.get('_readonly', 'false') == 'true'
        self.tab_order = int(element.get('tabindex', '0'))
        self.tool_tip_text = element.get('title')

    def is_really_enabled(self):
        return super().is_really_enabled() and self.parent.is_really_enabled()

    def _ais_setReadOnly(self, value):
        self.read_only = (value == 'true')
    def _ais_setTabOrder(self, value):
        self.tab_order = int(value)
    def _ais_setToolTipText(self, value):
        self.tool_tip_text = value

    def changed_properties(self):
        return ''

    def update_value_interactives(self):
        pass # TODO

    # TODO: We need a method to explicitly request firing a blur event.
    # (Find out which classes can fire it in webui.)

