from aisikl.components.control import Control
from aisikl.typeutils import ct, really_int
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class ProgressBar(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.maximum = ct(int, properties.get('maximum', 100))
        self.value = ct(int, properties.get('value', 0))

    def _ais_setMaximum(self, value: object) -> None:
        self.maximum = really_int(value)
    def _ais_setValue(self, value: object) -> None:
        self.value = min(self.maximum, really_int(value))
