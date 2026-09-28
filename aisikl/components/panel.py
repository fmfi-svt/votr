from aisikl.components.component import is_true
from aisikl.components.control import Control
from aisikl.events import action_event
from aisikl.operations import Operations
from aisikl.typeutils import ct, ct_none, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Panel(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.tab_id = ct_none(str, element.get('tabid'))
        self.title = ct_none(str, element.get('name'))
        # We only ever saw shortcut==None, but webui calls toUpperCase().
        self.shortcut = ct_none(str, properties.get('sctp'))
        self.autoscrolls = ct(bool, properties.get('autoscrolls', False))
        self.collapsable = ct(bool, properties.get('collapsable', False))
        self.collapsed = ct(bool, properties.get('collapsed', False))

    def _ais_setCollapsed(self, value: object) -> None:
        self.collapsed = is_true(value)

    async def toggle_collapsed(self, *, return_ops: bool = False) -> Operations:
        if not self.collapsable: return Operations()
        if not self.parent.is_really_enabled(): return Operations()
        await self.log('action', '{} {}'.format(
            'Opening' if self.collapsed else 'Closing', self.id))
        self.collapsed = not self.collapsed
        return await self._fire_event(return_ops=return_ops)

    async def _fire_event(self, *, return_ops: bool) -> Operations:
        self.dialog.component_changes(self, False)
        command = 'COLLAPSE' if self.collapsed else 'EXPAND'
        ev = action_event(self, command, self.id)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(collapsed=self.collapsed)
