
from __future__ import annotations
from .control import Control
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Label(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: dict[str, str | bool | int], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.shortcut = properties.get('sc')
        self.title_like_text = element.get('titleliketext')
        self.for_ = element.get('for')
        self.text = element.get_text()

    def _ais_setTitleLikeText(self, value):
        self.title_like_text = value
    def _ais_setFor(self, value):
        self.for_ = value

    def _ais_setImage(self, value):
        self.image = '/ais/images/' + value + '.png'
    def _ais_setUrl(self, value):
        self.image = value
