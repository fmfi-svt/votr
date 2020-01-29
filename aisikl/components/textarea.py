
from .textcontrol import TextControl


class TextArea(TextControl):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.value = element.get_text()

    def write(self, value):
        self.log('action', 'Writing {} in {}'.format(repr(value), self.id))
        self.value = value
        self.dialog.component_changes(self, False)

    def _ais_setText(self, value):
        self.value = value
        self.update_value_interactives('change')

    def changed_properties(self):
        if len(self.value) > self.max_length:
            self.value = self.value[0:self.max_length]

        return self._build_changed_properties(
            text=(None, True, self.value))
