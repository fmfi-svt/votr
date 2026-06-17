from aisikl.components.component import is_true
from aisikl.components.textinput import TextInput
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class DateControl(TextInput):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.min_value = properties.get('minValue')
        self.max_value = properties.get('maxValue')
        self.substitute_char = ct(str, properties.get('substituteChar', '_'))
        self.substitute_mask = ct(str, properties.get('substituteMask', '__.__.____'))
        self.mask = ct(str, properties.get('mask', 'dd.MM.yyyy'))
        self.calendar_enabled = ct(bool, properties.get('calendarEnabled', False))
        val = ct(str, nn(element).get('value', ''))
        self.value = '' if val == self.substitute_mask else val

    def _ais_setText(self, value: object) -> None:
        self.value = ct(str, value)
        self.update_value_interactives('change')
    def _ais_setSubstituteChar(self, value: object) -> None:
        self.substitute_char = ct(str, value or '_')[0:1]
    def _ais_setSubstituteMask(self, value: object) -> None:
        if value:
            value = ct(str, value)
            self.substitute_mask = value
            self.max_length = len(value)
    def _ais_setMask(self, value: object) -> None:
        self.mask = ct(str, value)
    def _ais_setCalendarEnabled(self, value: object) -> None:
        self.calendar_enabled = is_true(value)
    def _ais_setInvalidDateMessage(self, value: object) -> None:
        pass

    async def write(self, value: str) -> None:
        await self.log('action', f'Writing {value!r} in {self.id}')
        self.value = value
        self.dialog.component_changes(self, False)

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(
            text=(None, True, self.value))
