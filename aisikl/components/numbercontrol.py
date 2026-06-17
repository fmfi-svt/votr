from aisikl.components.component import is_true
from aisikl.components.textinput import TextInput
from aisikl.typeutils import ct, ct_none, nn, really_int
from typing import TYPE_CHECKING, Any, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


def maybe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class NumberControl(TextInput):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.separator_1000 = ct(str, element.get('separator1000', ' '))
        self.decimal_point = ct(str, element.get('decimalpoint', ','))
        self.scale = ct(int, properties.get('scale', 2))
        self.unit = properties.get('unit')
        self.negative_enabled = ct(bool, properties.get('negativeEnabled', True))
        self.min_value = maybe_float(ct(str, element.get('minvalue', '')))
        self.max_value = maybe_float(ct(str, element.get('maxvalue', '')))
        self.show_max_length = ct(int, properties.get('showMaxLength', 0))
        self.edit_max_length = ct(int, properties.get('editMaxLength', 0))
        self.bdvalue = ct_none(str, element.get('bdvalue'))

    def _ais_setSeparator1000(self, value: object) -> None:
        self.separator_1000 = ct(str, value)
    def _ais_setDecimalPoint(self, value: object) -> None:
        self.decimal_point = ct(str, value)
    def _ais_setScale(self, value: object) -> None:
        self.scale = really_int(value)
    def _ais_setUnit(self, value: object) -> None:
        self.unit = value
    def _ais_setNegativeEnabled(self, value: object) -> None:
        self.scale = is_true(value)
    def _ais_setMinValue(self, value: object) -> None:
        self.min_value = maybe_float(value)
    def _ais_setMaxValue(self, value: object) -> None:
        self.max_value = maybe_float(value)
    def _ais_setShowMaxLength(self, value: object) -> None:
        self.show_max_length = really_int(value)
    def _ais_setEditMaxLength(self, value: object) -> None:
        self.edit_max_length = really_int(value)
    def _ais_setLengths(self, show_max_length: object, edit_max_length: object) -> None:
        self.show_max_length = really_int(show_max_length)
        self.edit_max_length = really_int(edit_max_length)
    def _ais_setBDValue(self, value: object) -> None:
        self.bdvalue = ct(str, value)
    def _ais_setText(self, value: object) -> None:
        # For simplicity, we only do the simplest possible locale conversion.
        # Among other things, the setText function in AIS also:
        # - deletes leading "+"
        # - removes leading zeros
        # - removes trailing zeros from the fractional part
        # - removes decimal point if it's only followed by zeros
        # - re-appends the decimal point and/or trailing zeros until there are
        #   self.scale digits in the fractional part
        # - sets the value to "" if the fractional part length > self.scale
        # - sets the value to "" if length > self.edit_max_length
        value = ct(str, value)
        if self.separator_1000:
            value = value.replace(self.separator_1000, '')
        self.bdvalue = value.replace(self.decimal_point, '.')

    def write(self, bdvalue: str) -> None:
        self.log('action', f'Writing {bdvalue!r} in {self.id}')
        self.bdvalue = bdvalue
        self.dialog.component_changes(self, False)

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(
            value=(None, True, nn(self.bdvalue)))
