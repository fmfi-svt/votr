
from __future__ import annotations
from .control import Control
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class StackedPane(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: Dict[str, Union[int, str]], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.title = element.get('name')
