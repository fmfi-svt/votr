from aisikl.exceptions import AISParseError
from aisikl.typeutils import ct, ct_none, really_int
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


def is_true(value: object) -> bool:
    return value == 'true' or value == True


# TODO: Document Component and all subclasses.

class Component:
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        self.dialog = dialog
        self.id = id
        self.component_type = type
        self.used_listeners_mask = ct(int, properties.get('ulm', 0))
        self.enabled = ct(bool, properties.get('e', True))
        self.enabled_in_ui = ct(bool, properties.get('enabledInUI', True))
        self.visible = ct(bool, properties.get('v', True))
        self.visible_in_ui = ct(bool, properties.get('visibleInUI', True))
        self.title = ct_none(str, properties.get('title'))
        self.popup_menu = ct_none(str, properties.get('pm'))

        if properties.get('state', 1) == 2:
            raise AISParseError('STATE_DT is not supported')

    async def async_init(self, element: Tag | None) -> None:
        pass

    async def log(self, type: str, message: str, data: object=None, /) -> None:
        await self.dialog.app.ctx.log(type, message, data)

    def is_really_enabled(self) -> bool:
        return self.enabled and self.enabled_in_ui

    def _ais_setState(self, value: object) -> None:
        if really_int(value) == 2: raise AISParseError('STATE_DT is not supported')
    def _ais_setUsedListenersMask(self, value: object) -> None:
        self.used_listeners_mask = really_int(value)
    def _ais_setEnabled(self, value: object) -> None:
        self.enabled = is_true(value)
    def _ais_setEnabledInUI(self, value: object) -> None:
        self.enabled_in_ui = is_true(value)
    def _ais_setVisible(self, value: object) -> None:
        self.visible = is_true(value)
    def _ais_setVisibleInUI(self, value: object) -> None:
        self.visible_in_ui = is_true(value)
    def _ais_setTitle(self, value: object) -> None:
        self.title = ct_none(str, value)
    def _ais_setPopupMenu(self, value: object) -> None:
        self.popup_menu = ct_none(str, value)
