from typing import TYPE_CHECKING, override

from aisikl.components.textcontrol import TextControl
from aisikl.typeutils import ct, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class TextArea(TextControl):
    """A multi-line text box widget."""

    def __init__(
        self,
        dialog: Dialog,
        id: str,
        type: str,
        parent_id: str | None,
        properties: dict[str, object],
        element: Tag | None,
    ) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.value = nn(element).get_text()

    async def write(self, value: str) -> None:
        """Writes ``value`` in the box."""
        await self.log("action", f"Writing {value!r} in {self.id}")
        self.value = value
        self.dialog.component_changes(self, False)

    def _ais_setText(self, value: object) -> None:
        self.value = ct(str, value)
        self.update_value_interactives("change")

    @override
    def changed_properties(self) -> str:
        if len(self.value) > self.max_length:
            self.value = self.value[0 : self.max_length]

        return self._build_changed_properties(text=(None, True, self.value))
