from aisikl.components.control import Control
from aisikl.components.panel import Panel
from aisikl.events import change_action_event
from aisikl.typeutils import ct, nn, really_int
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class TabbedPane(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.selected_index = ct(int, properties.get('selectedIndex', 0))

        self.panel_ids = []
        arena = nn(element.find(id=ct(str, element['id']) + 'Arena', recursive=False))
        for panel in arena.find_all(id=True, recursive=False):
            self.panel_ids.append(panel['id'])

    def _ais_setSelectedIndex(self, value: object) -> None:
        self.selected_index = really_int(value)

    def select(self, index: int) -> None:
        self.log('action', 'Switching {} to tab {}'.format(self.id, index))
        self.selected_index = index
        self._fire_event()

    def get_panel(self, index: int) -> Panel:
        return ct(Panel, self.dialog.components[self.panel_ids[index]])
    def get_selected_panel(self) -> Panel:
        return self.get_panel(self.selected_index)

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(
            selectedIndex=str(self.selected_index))

    def _fire_event(self) -> None:
        self.dialog.component_changes(self, False)
        ev = change_action_event(self, self.selected_index)
        self.dialog.app.send_events(ev)
