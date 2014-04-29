
from aisikl.events import action_event
from .component import Component


class Action(Component):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.component_ids = element.get('components', '').split(',')
        self.accessible = element.get('accessible', 'true') == 'true'
        self.tool_tip_text = element.get('tooltiptext')
        self.confirm_question = element.get('confirmquestion')

    def get_components(self):
        return [self.dialog.components[id] for id in self.component_ids]

    def get_button_menu_item_js_objects(self):
        # TODO: Now that we don't follow webui names anyway (because they're
        # lower_case instead of camelCase), can we change this name?
        return [o for o in self.get_components()
                if o.jsct in ('button', 'menuItem')]

    def on_execute(self, original_source_name=None):
        '''Executes the action and emits the appropriate event.'''
        if not (self.accessible and self.enabled and self.enabled_in_ui and
                self.visible and self.visible_in_ui):
            return

        ev = action_event(self, None, original_source_name or self.id)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        self.dialog.app.send_events(ev)

    def _ais_setAccessible(self, value):
        self.accessible = (value == 'true')
    def _ais_setVisibleInUI(self, value):
        super()._ais_setVisibleInUI(value)
        for o in self.get_button_menu_item_js_objects():
            o._ais_setVisibleInUI(value)
    def _ais_setEnabledInUI(self, value):
        super()._ais_setEnabledInUI(value)
        for o in self.get_button_menu_item_js_objects():
            o._ais_setEnabledInUI(value)
    def _ais_setTitle(self, value):
        for o in self.get_button_menu_item_js_objects():
            if o.title == self.title:
                o._ais_setTitle(self, value)
        super()._ais_setTitle(value)
    def _ais_setToolTipText(self, value):
        for o in self.get_button_menu_item_js_objects():
            if o.tool_tip_text == self.tool_tip_text:
                o._ais_setToolTipText(value)
        self.tool_tip_text = value
    def _ais_setConfirmQuestion(self, value):
        for o in self.get_button_menu_item_js_objects():
            if o.confirm_question == self.confirm_question:
                o._ais_setConfirmQuestion(value)
        self.confirm_question = value
