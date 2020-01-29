
from .textinput import TextInput


class DateControl(TextInput):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.min_value = element.get('minvalue')
        self.max_value = element.get('maxvalue')
        self.substitute_char = element.get('substitutechar', '_')
        self.substitute_mask = element.get('substitutemask', '__.__.____')
        self.mask = element.get('mask', 'dd.MM.yyyy')
        self.calendar_enabled = properties.get('calendarEnabled', False)
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
        self.calendar_enabled = is_true(value)
    def _ais_setInvalidDateMessage(self, value):
        pass

    def write(self, value):
        self.log('action', 'Writing {} in {}'.format(repr(value), self.id))
        self.value = value
        self.dialog.component_changes(self, False)

    def changed_properties(self):
        return self._build_changed_properties(
            text=(None, True, self.value))
