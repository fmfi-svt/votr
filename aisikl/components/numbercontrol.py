
from .textinput import TextInput


def maybe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class NumberControl(TextInput):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.separator_1000 = element.get('separator1000', ' ')
        self.decimal_point = element.get('decimalpoint', ',')
        self.scale = int(element.get('scale', '2'))
        self.negative_enabled = element.get('negativeenabled', 'false') == 'true'
        self.min_value = maybe_float(element.get('minvalue', ''))
        self.max_value = maybe_float(element.get('maxvalue', ''))
        self.show_max_length = int(element.get('showmaxlength', '0'))
        self.edit_max_length = int(element.get('editmaxlength', '0'))
        self.bdvalue = element.get('bdvalue')

    def _ais_setSeparator1000(self, value):
        self.separator_1000 = value
    def _ais_setDecimalPoint(self, value):
        self.decimal_point = value
    def _ais_setScale(self, value):
        self.scale = int(value)
    def _ais_setNegativeEnabled(self, value):
        self.scale = (value == 'true')
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

    def write(self, value):
        self.log('action', 'Writing {} in {}'.format(repr(value), self.id))
        self.bdvalue = value
        self.dialog.component_changes(self, False)

    def changed_properties(self):
        return self._build_changed_properties(
            value=(None, True, self.bdvalue))
