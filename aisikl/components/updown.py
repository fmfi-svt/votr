from aisikl.components.control import Control
from aisikl.events import action_event
from aisikl.typeutils import ct, ct_none
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class UpDown(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_downed_component = ct_none(str, properties.get('upDownedComponent'))
        self.top_bottom_enabled = ct(bool, properties.get('topBottomEnabled', False))

    def click(self, command: str) -> None:
        if command not in ('UP', 'DOWN', 'TOP', 'BOTTOM'):
            raise ValueError('wrong UpDown command')
        self.log('action', 'Clicking {} {}'.format(self.id, command.lower()))
        if (
            (udc_id := self.up_downed_component) is not None and
            (udc := self.dialog.components.get(udc_id)) is not None
        ):
            udc.up_down_row(command)  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportUnknownMemberType, reportAttributeAccessIssue] # If it's not Table|CheckList, this will raise.
        else:
            ev = action_event(self, command, self.id)
            self.dialog.app.send_events(ev)

    def click_up(self) -> None:
        self.click('UP')

    def click_down(self) -> None:
        self.click('DOWN')

    def click_top(self) -> None:
        self.click('TOP')

    def click_bottom(self) -> None:
        self.click('BOTTOM')
