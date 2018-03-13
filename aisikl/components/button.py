
from aisikl.events import action_event
from .actionablecontrol import ActionableControl


class Button(ActionableControl):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.image = properties.get('img')
        self.confirm_question = element.get('confirmquestion')
        self.access_key = element.get('accesskey')

    def _ais_setAccessKey(self, value):
        self.access_key = value
    def _ais_setImage(self, value):
        self.image = value
    def _ais_setConfirmQuestion(self, value):
        self.confirm_question = value

    def click(self):
        self.log('action', 'Clicking {}'.format(self.id))

        if self.try_execute_action(): return

        ev = action_event(self, None, self.id)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        self.dialog.app.send_events(ev)

        # Note that showPopupMenus() is unsupported. Use menu items directly.
