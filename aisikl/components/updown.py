
from .control import Control
from aisikl.events import action_event


class UpDown(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.up_downed_component = element.get('updownedcomponent')

    def click(self, is_up):
        udc = self.dialog.components.get(self.up_downed_component)
        if udc and udc.up_down_row:
            udc.up_down_row(is_up)
        if not udc:
            ev = action_event(self, 'UP' if is_up else 'DOWN', self.id)
            self.dialog.app.send_events(ev)

    def click_up(self):
        self.click(True)

    def click_down(self):
        self.click(False)
