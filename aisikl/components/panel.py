
from __future__ import annotations
from .component import is_true
from .control import Control
from aisikl.events import action_event
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Panel(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: Dict[str, Union[str, bool, int]], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.tab_id = element.get('tabid')
        self.title = element.get('name')
        self.shortcut = properties.get('sctp')
        self.autoscrolls = properties.get('autoscrolls', False)
        self.collapsable = properties.get('collapsable', False)
        self.collapsed = properties.get('collapsed', False)

    def _ais_setCollapsed(self, value):
        self.collapsed = is_true(value)

    def toggle_collapsed(self):
        if not self.collapsable: return
        if not self.parent.is_really_enabled(): return
        self.log('action', '{} {}'.format(
            'Opening' if self.collapsed else 'Closing', self.id))
        self.collapsed = not self.collapsed
        self._fire_event()

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        command = 'COLLAPSE' if self.collapsed else 'EXPAND'
        ev = action_event(self, command, self.id)
        self.dialog.app.send_events(ev)

    def changed_properties(self):
        return self._build_changed_properties(collapsed=self.collapsed)
