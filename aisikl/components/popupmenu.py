from typing import TYPE_CHECKING

from aisikl.components.control import Control
from aisikl.events import component_event

if TYPE_CHECKING:
    from aisikl.operations import Operations


class PopupMenu(Control):
    """A WebUI popup menu.

    Aisikl generally doesn't keep track of which ``PopupMenu`` is open, or what
    item is selected. You can just access the
    [`MenuItem`][aisikl.components.menuitem.MenuItem] you want directly -- you
    don't have to open its menu first.

    webui.js has theoretical supports for popup menus that emit events when they
    are opened or closed. Empirically, this was never seen (all known menus have
    ``used_listeners_mask == 0``). In the unlikely scenario that you find a
    popup menu with a nonzero ``used_listeners_mask``, and the AIS server does
    something useful upon receiving the events, you can manually trigger them
    with [`show`][] and [`hide`][].
    """

    async def show(self, *, return_ops: bool = False) -> Operations:
        """Opens the menu. Usually not needed, see above."""
        await self.log("action", f"Opening {self.id}")
        ev = component_event(self, "init", "INIT")
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def hide(self, *, return_ops: bool = False) -> Operations:
        """Closes the menu. Usually not needed, see above."""
        await self.log("action", f"Closing {self.id}")
        ev = component_event(self, "beforeclose", "BEFORECLOSE")
        return await self.dialog.app.send_events(ev, return_ops=return_ops)
