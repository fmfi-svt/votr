
from __future__ import annotations
from .control import Control
from aisikl.events import action_event
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class UpDown(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: Dict[str, Union[str, bool, int]], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_downed_component = properties.get('upDownedComponent')
        self.top_bottom_enabled = properties.get('topBottomEnabled', False)

    def click(self, command):
        if command not in ('UP', 'DOWN', 'TOP', 'BOTTOM'):
            raise ValueError('wrong UpDown command')
        self.log('action', 'Clicking {} {}'.format(self.id, command.lower()))
        udc = self.dialog.components.get(self.up_downed_component)
        if udc:
            udc.up_down_row(command)
        else:
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
