from typing import TYPE_CHECKING, override

from aisikl.components.actionablecontrol import ActionableControl
from aisikl.typeutils import ct, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class HtmlArea(ActionableControl):
    """A box that can contain arbitrary HTML content."""

    content: str

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
        self.safe_links = ct(bool, properties.get("safeLinks", False))
        """If false, HTML links will open in a new window."""
        self._parse_content(nn(element))
        # Note: This is where we should call component_changes() if we actually
        # supported canClose.

    def _parse_content(self, element: Tag) -> None:
        self.content = nn(element.find(id="htmlContent")).get_text()[4:-3]

    def _ais_setHtml(self, id: str, body: Tag) -> None:
        self._parse_content(nn(body.find(id=id)))

    _ais_setHtml.wants_body = True  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportFunctionMemberAccess]

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(canClose=self.can_close)

    @property
    def can_close(self) -> bool:
        """Unknown meaning. Not implemented."""
        # canClose is actually determined by a script running in the iframe.
        # Since we don't run anything, we don't support canClose.
        raise Exception("canClose is unsupported")
