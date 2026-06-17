from aisikl.events import action_event
from aisikl.components.actionablecontrol import ActionableControl
from aisikl.typeutils import ct_none, nn
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Button(ActionableControl):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.image = ct_none(str, properties.get('img'))
        # We only ever saw shortcut==None, but webui calls toUpperCase().
        self.shortcut = ct_none(str, properties.get('sc'))
        self.confirm_question = ct_none(str, element.get('confirmquestion'))
        self.access_key = element.get('accesskey')
        if isinstance(self.access_key, list):
            self.access_key = ' '.join(self.access_key)  # BeautifulSoup :(

    def _ais_setAccessKey(self, value: object) -> None:
        self.access_key = ct_none(str, value)
    def _ais_setImage(self, value: object) -> None:
        self.image = ct_none(str, value)
    def _ais_setConfirmQuestion(self, value: object) -> None:
        self.confirm_question = ct_none(str, value)

    async def click(self) -> None:
        await self.log('action', f'Clicking {self.id}')

        if await self.try_execute_action(): return

        ev = action_event(self, None, self.id)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        await self.dialog.app.send_events(ev)

        # Note that showPopupMenus() is unsupported. Use menu items directly.
