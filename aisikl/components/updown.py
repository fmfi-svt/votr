from typing import TYPE_CHECKING, Literal

from aisikl.components.checklist import CheckList
from aisikl.components.control import Control
from aisikl.components.table import Table
from aisikl.events import action_event
from aisikl.typeutils import ct, ct_none

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog
    from aisikl.operations import Operations


class UpDown(Control):
    """A group of buttons used to change the order of elements in some list."""

    def __init__(
        self,
        dialog: Dialog,
        id: str,
        type: str,
        parent_id: str | None,
        properties: dict[str, object],
        element: Tag | None,
    ) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_downed_component = ct_none(
            str, properties.get("upDownedComponent"))
        """The component ID controlled by these buttons."""
        self.top_bottom_enabled = ct(
            bool, properties.get("topBottomEnabled", False))
        """Whether "move to top" and "move to bottom" buttons also exist."""

    async def click(
        self,
        command: Literal["UP", "DOWN", "TOP", "BOTTOM"],
        *,
        return_ops: bool = False,
    ) -> Operations:
        """Clicks one of the buttons, moving the selected item in the list."""
        await self.log("action", f"Clicking {self.id} {command.lower()}")
        if (  #
            (udc_id := self.up_downed_component) is not None
            and (udc := self.dialog.components.get(udc_id)) is not None
        ):
            if isinstance(udc, (Table, CheckList)):
                return await udc.up_down_row(command, return_ops=return_ops)
            raise TypeError(
                f"expected Table or CheckList instead of {type(udc).__name__}")
        else:
            ev = action_event(self, command, self.id)
            return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def click_up(self, *, return_ops: bool = False) -> Operations:
        """Clicks the up arrow button, moving the item up by one."""
        return await self.click("UP", return_ops=return_ops)

    async def click_down(self, *, return_ops: bool = False) -> Operations:
        """Clicks the down arrow button, moving the item down by one."""
        return await self.click("DOWN", return_ops=return_ops)

    async def click_top(self, *, return_ops: bool = False) -> Operations:
        """Clicks the top button, moving the item to the top."""
        return await self.click("TOP", return_ops=return_ops)

    async def click_bottom(self, *, return_ops: bool = False) -> Operations:
        """Clicks the bottom button, moving the item to the bottom."""
        return await self.click("BOTTOM", return_ops=return_ops)
