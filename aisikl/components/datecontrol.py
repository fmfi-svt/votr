
from .textinput import TextInput


class DateControl(TextInput):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.min_value = element.get('minvalue')
        self.max_value = element.get('maxvalue')
        self.substitute_char = element.get('substituteChar', '_')
        self.substitute_mask = element.get('substituteMask', '__.__.____')
        self.mask = element.get('mask', 'dd.MM.yyyy')
        self.calendar_enabled = element.get('calendarEnabled', 'false') == 'true'
        val = element.get('value', '')
        self.value = '' if val == self.substitute_mask else val

    def _ais_setText(self, value):
        self.value = value
        self.update_value_interactives('change')
    def _ais_setSubstituteChar(self, value):
        self.substitute_char = (value or '_')[0:1]
    def _ais_setSubstituteMask(self, value):
        if value:
            self.substitute_mask = value
            self.max_length = len(value)
    def _ais_setMask(self, value):
        self.mask = value
    def _ais_setCalendarEnabled(self, value):
        self.calendar_enabled = (value == 'true')
    def _ais_setInvalidDateMessage(self, value):
        pass

    def write(self, value):
        self.log('action', 'Writing {} in {}'.format(repr(value), self.id))
        self.value = value
        self.dialog.component_changes(self, False)

    def changed_properties(self):
        return self._build_changed_properties(
            text=(None, True, self.value))
