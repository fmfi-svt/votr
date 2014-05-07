
from aisikl.events import item_event
from .control import Control


class CheckBox(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        input = element.input
        self.smoked = input.get('smoked', 'false') == 'true'
        self.selected = input.has_attr('checked')
        self.image = element.get('_image')
        self.confirm_question = element.get('confirmquestion')

    def _ais_setSmoked(self, value):
        self.smoked = (value == 'true')
    def _ais_setSelected(self, value):
        self.selected = (value == 'true')
        self.dialog.try_interactive(self, "ItemEvent")

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        ev = item_event(self)
        self.dialog.app.send_events(ev)

    def changed_properties(self):
        return self._build_changed_properties(
            selected=self.selected, smoked=self.smoked)

    def toggle(self):
        self.selected = not self.selected
        self.smoked = False
        self._fire_event()

    def set_to(self, value):
        if self.smoked or self.selected != bool(value):
            self.selected = bool(value)
            self.smoked = False
            self._fire_event()
