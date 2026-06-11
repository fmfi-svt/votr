
from __future__ import annotations
from aisikl.events import item_event
from .component import is_true
from .control import Control
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class CheckBox(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: Dict[str, Union[str, bool, int]], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.shortcut = properties.get('sc')
        input = element.input
        self.smoked = input.get('smoked', 'false') == 'true'
        self.selected = input.has_attr('checked')

    def _ais_setSmoked(self, value):
        self.smoked = is_true(value)
    def _ais_setSelected(self, value):
        self.selected = is_true(value)
        self.dialog.try_interactive(self, "ItemEvent")

    def _fire_event(self) -> None:
        self.dialog.component_changes(self, False)
        ev = item_event(self)
        self.dialog.app.send_events(ev)

    def changed_properties(self) -> str:
        return self._build_changed_properties(
            selected=self.selected, smoked=self.smoked)

    def toggle(self):
        self.selected = not self.selected
        self.smoked = False
        self.log('action', '{} {}'.format(
            'Checking' if self.selected else 'Unchecking', self.id))
        self._fire_event()

    def set_to(self, value: bool) -> None:
        if self.smoked or self.selected != bool(value):
            self.selected = bool(value)
            self.smoked = False
            self.log('action', '{} {}'.format(
                'Checking' if self.selected else 'Unchecking', self.id))
            self._fire_event()
