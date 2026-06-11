from aisikl.components.textcontrol import TextControl
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class TextArea(TextControl):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.value = nn(element).get_text()

    def write(self, value: str) -> None:
        self.log('action', 'Writing {} in {}'.format(repr(value), self.id))
        self.value = value
        self.dialog.component_changes(self, False)

    def _ais_setText(self, value: object) -> None:
        self.value = ct(str, value)
        self.update_value_interactives('change')

    @override
    def changed_properties(self) -> str:
        if len(self.value) > self.max_length:
            self.value = self.value[0:self.max_length]

        return self._build_changed_properties(
            text=(None, True, self.value))
