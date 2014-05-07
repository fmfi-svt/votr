
from .control import Control


class TextControl(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.max_length = int(element.get('maxlength', '65536')) or 65536
        self.tool_tip_like_text = element.get('ttlt', 'false') == 'true'
        self.enter_to_next = element.get('entertonext', 'false') == 'true'
        self.placeholder = element.get('_placeholder')

    def _ais_setMaxLength(self, value):
        self.max_length = int(value) or 65536
    def _ais_setToolTipLikeText(self, value):
        self.tool_tip_like_text = (value == 'true')
    def _ais_setEnterToNext(self, value):
        self.enter_to_next = (value == 'true')
    def _ais_setDefaultBackground(self, value):
        pass
    def _ais_setReadOnlyBackground(self, value):
        pass
    def _ais_setPlaceHolder(self, value):
        self.placeholder = value

    def is_editable(self):
        return self.is_really_enabled() and not self.read_only
