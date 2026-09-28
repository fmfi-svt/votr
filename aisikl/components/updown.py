from aisikl.components.checklist import CheckList
from aisikl.components.control import Control
from aisikl.components.table import Table
from aisikl.events import action_event
from aisikl.typeutils import ct, ct_none
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from aisikl.operations import Operations
    from bs4.element import Tag


class UpDown(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_downed_component = ct_none(str, properties.get('upDownedComponent'))
        self.top_bottom_enabled = ct(bool, properties.get('topBottomEnabled', False))

    async def click(self, command: str, *, return_ops: bool = False) -> Operations:
        if command not in ('UP', 'DOWN', 'TOP', 'BOTTOM'):
            raise ValueError('wrong UpDown command')
        await self.log('action', f'Clicking {self.id} {command.lower()}')
        if (
            (udc_id := self.up_downed_component) is not None and
            (udc := self.dialog.components.get(udc_id)) is not None
        ):
            if isinstance(udc, (Table, CheckList)):
                return await udc.up_down_row(command, return_ops=return_ops)
            raise TypeError(
                f"expected Table or CheckList instead of {type(udc).__name__}")
        else:
            ev = action_event(self, command, self.id)
            return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def click_up(self, *, return_ops: bool = False) -> Operations:
        return await self.click('UP', return_ops=return_ops)

    async def click_down(self, *, return_ops: bool = False) -> Operations:
        return await self.click('DOWN', return_ops=return_ops)

    async def click_top(self, *, return_ops: bool = False) -> Operations:
        return await self.click('TOP', return_ops=return_ops)

    async def click_bottom(self, *, return_ops: bool = False) -> Operations:
        return await self.click('BOTTOM', return_ops=return_ops)
