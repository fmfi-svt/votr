from aisikl.components.control import Control
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Image(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.image = ct(str, nn(nn(element).img).get('src', ''))

    def _ais_setImage(self, value: object) -> None:
        self.image = '/ais/images/' + ct(str, value) + '.png'
    def _ais_setUrl(self, value: object) -> None:
        self.image = ct(str, value)
