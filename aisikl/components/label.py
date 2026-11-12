from typing import TYPE_CHECKING

from aisikl.components.control import Control
from aisikl.typeutils import ct_none, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class Label(Control):
    """A static WebUI label."""

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
        element = nn(element)
        self.shortcut = properties.get("sc")
        """Key shortcut, probably. Empirically, it's always ``None``."""
        self.title_like_text = ct_none(str, element.get("titleliketext"))
        self.for_ = ct_none(str, element.get("for"))
        """The component ID to focus when clicking the label in the AIS UI."""
        self.text = element.get_text()
        """Label content."""

    def _ais_setTitleLikeText(self, value: object) -> None:
        self.title_like_text = ct_none(str, value)

    def _ais_setFor(self, value: object) -> None:
        self.for_ = ct_none(str, value)
