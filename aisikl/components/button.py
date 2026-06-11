
from __future__ import annotations
from aisikl.events import action_event
from .actionablecontrol import ActionableControl
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Button(ActionableControl):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: Dict[str, Union[str, bool, int]], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.image = properties.get('img')
        self.shortcut = properties.get('sc')
        self.confirm_question = element.get('confirmquestion')
        self.access_key = element.get('accesskey')
        if isinstance(self.access_key, list):
            self.access_key = ' '.join(self.access_key)  # BeautifulSoup :(

    def _ais_setAccessKey(self, value):
        self.access_key = value
    def _ais_setImage(self, value: str) -> None:
        self.image = value
    def _ais_setConfirmQuestion(self, value):
        self.confirm_question = value

    def click(self) -> None:
        self.log('action', 'Clicking {}'.format(self.id))

        if self.try_execute_action(): return

        ev = action_event(self, None, self.id)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        self.dialog.app.send_events(ev)

        # Note that showPopupMenus() is unsupported. Use menu items directly.
