from aisikl.events import action_event
from aisikl.components.actionablecontrol import ActionableControl
from aisikl.typeutils import ct_none
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class MenuItem(ActionableControl):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.popup_menu_id = properties.get('pmid')
        # We only ever saw confirm_question==None, but webui calls confirm().
        self.confirm_question = ct_none(str, properties.get('confirmQuestion'))
        # We only ever saw image==None, but webui uses it as a string to build the src.
        self.image = ct_none(str, properties.get('image'))

    def _ais_setConfirmQuestion(self, value: object) -> None:
        self.confirm_question = ct_none(str, value)
    def _ais_setImage(self, value: object) -> None:
        self.image = ct_none(str, value)

    def click(self, params: str | None=None) -> None:
        self.log('action', 'Clicking {}'.format(self.id))

        if self.try_execute_action(params): return

        ev = action_event(self, None, self.id, params)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        self.dialog.app.send_events(ev)
