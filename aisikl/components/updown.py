
from .control import Control
from aisikl.events import action_event


class UpDown(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.up_downed_component = element.get('updownedcomponent')
        self.top_bottom_enabled = element.get('topbottomenabled', 'false') == 'true'

    def click(self, command):
        if command not in ('UP', 'DOWN', 'TOP', 'BOTTOM'):
            raise ValueError('wrong UpDown command')
        self.log('action', 'Clicking {} {}'.format(self.id, command.lower()))
        udc = self.dialog.components.get(self.up_downed_component)
        if udc and udc.up_down_row:
            udc.up_down_row(command)
        if not udc:
            ev = action_event(self, command, self.id)
            self.dialog.app.send_events(ev)

    def click_up(self):
        self.click('UP')

    def click_down(self):
        self.click('DOWN')

    def click_top(self):
        self.click('TOP')

    def click_bottom(self):
        self.click('BOTTOM')
