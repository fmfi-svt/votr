from typing import TYPE_CHECKING

from aisikl.components.actionablecontrol import ActionableControl
from aisikl.events import action_event
from aisikl.typeutils import ct_none, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog
    from aisikl.operations import Operations


class Button(ActionableControl):
    """A WebUI button."""

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
        self.image = ct_none(str, properties.get("img"))
        """Button icon symbolic name. E.g. "run" for the runner icon."""
        # We only ever saw shortcut==None, but webui calls toUpperCase().
        self.shortcut = ct_none(str, properties.get("sc"))
        """Key shortcut, probably. Empirically, it's always ``None``."""
        self.confirm_question = ct_none(str, element.get("confirmquestion"))
        """AIS UI asks this question when the button is clicked, before sending
        the event. Empirically, it's always ``None``. The AIS UI generally uses
        [`ConfirmBoxOp`][aisikl.operations.ConfirmBoxOp] instead.
        """
        self.access_key = element.get("accesskey")
        """Key shortcut (with ``Alt``)."""
        if isinstance(self.access_key, list):
            self.access_key = " ".join(self.access_key)  # BeautifulSoup :(

    def _ais_setAccessKey(self, value: object) -> None:
        self.access_key = ct_none(str, value)

    def _ais_setImage(self, value: object) -> None:
        self.image = ct_none(str, value)

    def _ais_setConfirmQuestion(self, value: object) -> None:
        self.confirm_question = ct_none(str, value)

    async def click(self, *, return_ops: bool = False) -> Operations:
        """Clicks the button.

        If the button just opens a popup menu, you don't have to click it.
        Aisikl doesn't track which popup menus are open.

        If [`confirm_question`][] is not ``None``, ``click`` ignores it --
        effectively answering "yes". You should show your own confirmation UI
        before dangerous actions.
        """
        await self.log("action", f"Clicking {self.id}")

        did, ops = await self._try_execute_action(return_ops=return_ops)
        if did:
            return ops

        ev = action_event(self, None, self.id)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)
