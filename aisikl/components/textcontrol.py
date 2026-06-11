from aisikl.components.component import is_true
from aisikl.components.control import Control
from aisikl.typeutils import ct, ct_none, nn, really_int
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class TextControl(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.max_length = int(ct(str, nn(element).get('maxlength', '65536'))) or 65536
        self.tool_tip_like_text = ct(bool, properties.get('ttlt', False))
        self.enter_to_next = ct(bool, properties.get('enterToNext', False))
        self.placeholder = ct_none(str, properties.get('placeHolder'))

    def _ais_setMaxLength(self, value: object) -> None:
        self.max_length = really_int(value or 65536) or 65536
    def _ais_setToolTipLikeText(self, value: object) -> None:
        self.tool_tip_like_text = is_true(value)
    def _ais_setEnterToNext(self, value: object) -> None:
        self.enter_to_next = is_true(value)
    def _ais_setDefaultBackground(self, value: object) -> None:
        pass
    def _ais_setReadOnlyBackground(self, value: object) -> None:
        pass
    def _ais_setPlaceHolder(self, value: object) -> None:
        self.placeholder = ct_none(str, value)

    def is_editable(self) -> bool:
        return self.is_really_enabled() and not self.read_only
