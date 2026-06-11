
from __future__ import annotations
from .control import Control
from aisikl.events import change_action_event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class TabbedPane(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: dict[str, int | str], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.selected_index = properties.get('selectedIndex', 0)

        self.panel_ids = []
        arena = element.find(id=element['id'] + 'Arena', recursive=False)
        for panel in arena.find_all(id=True, recursive=False):
            self.panel_ids.append(panel['id'])

    def _ais_setSelectedIndex(self, value):
        self.selected_index = int(value)

    def select(self, index):
        self.log('action', 'Switching {} to tab {}'.format(self.id, index))
        self.selected_index = index
        self._fire_event()

    def get_panel(self, index):
        return self.dialog.components[self.panel_ids[index]]
    def get_selected_panel(self):
        return self.get_panel(self.selected_index)

    def changed_properties(self):
        return self._build_changed_properties(
            selectedIndex=str(self.selected_index))

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        ev = change_action_event(self, self.selected_index)
        self.dialog.app.send_events(ev)
