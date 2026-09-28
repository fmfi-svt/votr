from aisikl.components.control import Control
from aisikl.components.panel import Panel
from aisikl.events import change_action_event
from aisikl.typeutils import ct, nn, really_int
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from aisikl.operations import Operations
    from bs4.element import Tag


class TabbedPane(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.selected_index = ct(int, properties.get('selectedIndex', 0))

        self.panel_ids: list[str] = []
        arena = nn(element.find(id=ct(str, element['id']) + 'Arena', recursive=False))
        for panel in arena.find_all(id=True, recursive=False):
            self.panel_ids.append(ct(str, panel['id']))

    def _ais_setSelectedIndex(self, value: object) -> None:
        self.selected_index = really_int(value)

    async def select(self, index: int, *, return_ops: bool = False) -> Operations:
        await self.log('action', f'Switching {self.id} to tab {index}')
        self.selected_index = index
        return await self._fire_event(return_ops=return_ops)

    def get_panel(self, index: int) -> Panel:
        return ct(Panel, self.dialog.components[self.panel_ids[index]])
    def get_selected_panel(self) -> Panel:
        return self.get_panel(self.selected_index)

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(
            selectedIndex=str(self.selected_index))

    async def _fire_event(self, *, return_ops: bool) -> Operations:
        self.dialog.component_changes(self, False)
        ev = change_action_event(self, self.selected_index)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)
