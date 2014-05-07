
from .textinput import TextInput


class TextField(TextInput):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.label_display = element.get('labeldisplay')
        self.value = element.get('value', '')
        if element.get('type') == 'password':
            self.type = 'password'
        else:
            self.type = element.get('xtype')
        self.suggestions_enabled = element.get('suggestionsenabled', 'false') == 'true'
        self.suggestions_multi_value_enabled = element.get('suggestionsmultivalueenabled', 'false') == 'true'
        self.tool_tip_changed = False

    def _ais_setLabelDisplay(self, value):
        self.label_display = value
    def _ais_setText(self, value):
        self.value = value
        self.update_value_interactives('change')
    def _ais_setType(self, value):
        self.type = value
    def _ais_setSuggestionsEnabled(self, value):
        self.suggestions_enabled = (value == 'true')
    def _ais_setSuggestionsMultiValueEnabled(self, value):
        self.suggestions_multi_value_enabled = (value == 'true')

    def _mark_changed(self):
        # This function makes no sense. It's webui's fault.
        if self.label_display:
            label = self.dialog.components[self.label_display]
            if label:
                label.text = ''
                label.title_like_text = ''

        self.dialog.component_changes(self, False)
        if self.tool_tip_like_text:
            self.tool_tip_changed = True
            self.tool_tip_text = ''

    def write(self, value):
        self.value = value
        self._mark_changed()

    def changed_properties(self):
        ch = dict(text=(None, True, self.value))
        if self.tool_tip_changed:
            ch['toolTipText'] = (None, True, self.tool_tip_text)
            self.tool_tip_changed = False
        return self._build_changed_properties(**ch)
