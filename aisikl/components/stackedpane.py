from typing import TYPE_CHECKING

from aisikl.components.control import Control
from aisikl.typeutils import ct_none, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class StackedPane(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.title = ct_none(str, nn(element).get("name"))
