
from __future__ import annotations
from aisikl.events import action_event
from .actionablecontrol import ActionableControl
from typing import TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class MenuItem(ActionableControl):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str, properties: Dict[str, Union[bool, str]], element: Tag) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.popup_menu_id = properties.get('pmid')
        self.confirm_question = properties.get('confirmQuestion')
        self.image = properties.get('image')

    def _ais_setConfirmQuestion(self, value):
        self.confirm_question = value
    def _ais_setImage(self, value):
        self.image = value

    def click(self, params: None=None) -> None:
        self.log('action', 'Clicking {}'.format(self.id))

        if self.try_execute_action(params): return

        ev = action_event(self, None, self.id, params)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        self.dialog.app.send_events(ev)
