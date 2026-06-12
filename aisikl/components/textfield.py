from aisikl.components.component import is_true
from aisikl.components.label import Label
from aisikl.components.textinput import TextInput
from aisikl.typeutils import ct, ct_none, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class TextField(TextInput):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.label_display = ct_none(str, element.get('labeldisplay'))
        self.value = ct(str, element.get('value', ''))
        self.type: str | None
        if element.get('type') == 'password':
            self.type = 'password'
        else:
            self.type = ct_none(str, element.get('xtype'))
        self.suggestions_enabled = ct(bool, properties.get('suggestionsEnabled', False))
        self.suggestions_multi_value_enabled = ct(bool, properties.get('suggestionsMultiValueEnabled', True))
        self.tool_tip_changed = False

    def _ais_setLabelDisplay(self, value: object) -> None:
        self.label_display = ct_none(str, value)
    def _ais_setText(self, value: object) -> None:
        self.value = ct(str, value)
        self.update_value_interactives('change')
    def _ais_setType(self, value: object) -> None:
        self.type = ct_none(str, value)
    def _ais_setSuggestionsEnabled(self, value: object) -> None:
        self.suggestions_enabled = is_true(value)
    def _ais_setSuggestionsMultiValueEnabled(self, value: object) -> None:
        self.suggestions_multi_value_enabled = is_true(value)

    def _mark_changed(self) -> None:
        # This function makes no sense. It's webui's fault.
        if self.label_display:
            label = self.dialog.components[self.label_display]
            if label:
                ct(Label, label).text = ''
                ct(Label, label).title_like_text = ''

        self.dialog.component_changes(self, False)
        if self.tool_tip_like_text:
            self.tool_tip_changed = True
            self.tool_tip_text: str | None = ''

    def write(self, value: str) -> None:
        self.log('action', 'Writing {} in {}'.format(repr(value), self.id))
        self.value = value
        self._mark_changed()

    @override
    def changed_properties(self) -> str:
        ch = dict(text=(None, True, self.value))
        if self.tool_tip_changed:
            ch['toolTipText'] = (None, True, nn(self.tool_tip_text))
            self.tool_tip_changed = False
        return self._build_changed_properties(**ch)
