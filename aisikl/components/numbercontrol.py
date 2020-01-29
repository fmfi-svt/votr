
from .component import is_true
from .textinput import TextInput


def maybe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class NumberControl(TextInput):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.separator_1000 = element.get('separator1000', ' ')
        self.decimal_point = element.get('decimalpoint', ',')
        self.scale = properties.get('scale', 2)
        self.unit = properties.get('unit')
        self.negative_enabled = properties.get('negativeEnabled', True)
        self.min_value = maybe_float(element.get('minvalue', ''))
        self.max_value = maybe_float(element.get('maxvalue', ''))
        self.show_max_length = properties.get('showMaxLength', 0)
        self.edit_max_length = properties.get('editMaxLength', 0)
        self.bdvalue = element.get('bdvalue')

    def _ais_setSeparator1000(self, value):
        self.separator_1000 = value
    def _ais_setDecimalPoint(self, value):
        self.decimal_point = value
    def _ais_setScale(self, value):
        self.scale = int(value)
    def _ais_setUnit(self, value):
        self.unit = value
    def _ais_setNegativeEnabled(self, value):
        self.scale = is_true(value)
    def _ais_setMinValue(self, value):
        self.min_value = maybe_float(value)
    def _ais_setMaxValue(self, value):
        self.max_value = maybe_float(value)
    def _ais_setShowMaxLength(self, value):
        self.show_max_length = int(value)
    def _ais_setEditMaxLength(self, value):
        self.edit_max_length = int(value)
    def _ais_setLengths(self, show_max_length, edit_max_length):
        self.show_max_length = int(show_max_length)
        self.edit_max_length = int(edit_max_length)
    def _ais_setBDValue(self, value):
        self.bdvalue = value
    def _ais_setText(self, value):
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
        if self.separator_1000:
            value = value.replace(self.separator_1000, '')
        self.bdvalue = value.replace(self.decimal_point, '.')

    def write(self, bdvalue):
        self.log('action', 'Writing {} in {}'.format(repr(bdvalue), self.id))
        self.bdvalue = bdvalue
        self.dialog.component_changes(self, False)

    def changed_properties(self):
        return self._build_changed_properties(
            value=(None, True, self.bdvalue))
