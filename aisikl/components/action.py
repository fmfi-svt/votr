
from aisikl.events import action_event
from .component import Component, is_true


class Action(Component):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.accessible = properties.get('accessible', True)
        self.tool_tip_text = properties.get('toolTipText')
        self.shortcut = properties.get('sc')
        self.action_list_id = properties.get('actionListId')
        self.confirm_question = properties.get('confirmQuestion')
        self.component_ids = properties.get('cids')

    def get_components(self):
        return [self.dialog.components[id] for id in self.component_ids]

    def get_buttons_and_menu_items(self):
        return [o for o in self.get_components()
                if o.component_type in ('button', 'menuItem')]

    def execute(self, original_source_name=None, params=None):
        '''Executes the action and emits the appropriate event.'''
        if not (self.accessible and self.enabled and self.enabled_in_ui and
                self.visible and self.visible_in_ui):
            # TODO: we should return here, but we can only do that once we
            # properly support interactives. for now, the developer knows best.
            pass

        if not original_source_name:
            self.log('action', 'Executing {}'.format(self.id))

        ev = action_event(self, None, original_source_name or self.id, params)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        self.dialog.app.send_events(ev)

    def _ais_setAccessible(self, value):
        self.accessible = is_true(value)
    def _ais_setVisibleInUI(self, value):
        super()._ais_setVisibleInUI(value)
        for o in self.get_buttons_and_menu_items():
            o._ais_setVisibleInUI(value)
    def _ais_setEnabledInUI(self, value):
        super()._ais_setEnabledInUI(value)
        for o in self.get_buttons_and_menu_items():
            o._ais_setEnabledInUI(value)
    def _ais_setTitle(self, value):
        for o in self.get_buttons_and_menu_items():
            if o.title == self.title:
                o._ais_setTitle(self, value)
        super()._ais_setTitle(value)
    def _ais_setToolTipText(self, value):
        for o in self.get_buttons_and_menu_items():
            if o.tool_tip_text == self.tool_tip_text:
                o._ais_setToolTipText(value)
        self.tool_tip_text = value
    def _ais_setConfirmQuestion(self, value):
        for o in self.get_buttons_and_menu_items():
            if o.confirm_question == self.confirm_question:
                o._ais_setConfirmQuestion(value)
        self.confirm_question = value
