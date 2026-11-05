from aisikl.events import action_event
from aisikl.components.actionablecontrol import ActionableControl
from aisikl.typeutils import ct_none
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from aisikl.operations import Operations
    from bs4.element import Tag


class MenuItem(ActionableControl):
    """A WebUI popup menu item."""

    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.popup_menu_id = properties.get('pmid')
        # We only ever saw confirm_question==None, but webui calls confirm().
        self.confirm_question = ct_none(str, properties.get('confirmQuestion'))
        """AIS UI asks this question when the menu item is clicked, before
        sending the event. Empirically, it's always ``None``. The AIS UI
        generally uses [`ConfirmBoxOp`][aisikl.operations.ConfirmBoxOp] instead.
        """
        # We only ever saw image==None, but webui uses it as a string to build
        # the src. Hence we type it as `str | None`.
        self.image = ct_none(str, properties.get('image'))
        """Menu item icon symbolic name. Empirically, it's always ``None``."""

    def _ais_setConfirmQuestion(self, value: object) -> None:
        self.confirm_question = ct_none(str, value)
    def _ais_setImage(self, value: object) -> None:
        self.image = ct_none(str, value)

    async def click(self, params: str | None=None, *, return_ops: bool = False) -> Operations:
        """Clicks the menu item.

        If [`confirm_question`][] is not ``None``, ``click`` ignores it --
        effectively answering "yes". You should show your own confirmation UI
        before dangerous actions.

        Args:
            params: Extra data for popup menus opened by
                [`HtmlArea`][aisikl.components.htmlarea.HtmlArea]. Corresponds
                to the fourth argument of the webui.js function
                ``tryShowPopupMenuFromHtmlArea(area, event, menu, params)``,
                which presumably can be called from scripts in the
                ``HtmlArea``'s HTML content. Empirically, no known ``HtmlArea``
                uses this.
            return_ops: See [`aisikl.operations`][].
        """
        await self.log('action', f'Clicking {self.id}')

        did, ops = await self._try_execute_action(return_ops=return_ops)
        if did:
            return ops

        ev = action_event(self, None, self.id, params)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)
