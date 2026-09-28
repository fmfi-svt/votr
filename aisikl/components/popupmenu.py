from aisikl.components.control import Control
from aisikl.events import component_event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.operations import Operations


class PopupMenu(Control):
    async def show(self, *, return_ops: bool = False) -> Operations:
        # Some menus emit an "init" event when opened. You can do that with
        # this function, but you must do it manually when needed. By default,
        # menu items can be accessed directly without opening the menu first.
        await self.log('action', f'Opening {self.id}')
        ev = component_event(self, 'init', 'INIT')
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def hide(self, *, return_ops: bool = False) -> Operations:
        # Some menus emit a "beforeclose" event when closed. You can do that
        # with this function, but you must do it manually when needed. By
        # default, menus do not need to be opened and closed explicitly.
        await self.log('action', f'Closing {self.id}')
        ev = component_event(self, 'beforeclose', 'BEFORECLOSE')
        return await self.dialog.app.send_events(ev, return_ops=return_ops)
