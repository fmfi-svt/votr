
from .component import is_true
from .control import Control


class TextControl(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.max_length = int(element.get('maxlength', '65536')) or 65536
        self.tool_tip_like_text = properties.get('ttlt', False)
        self.enter_to_next = properties.get('enterToNext', False)
        self.placeholder = properties.get('placeHolder')

    def _ais_setMaxLength(self, value):
        self.max_length = int(value) or 65536
    def _ais_setToolTipLikeText(self, value):
        self.tool_tip_like_text = is_true(value)
    def _ais_setEnterToNext(self, value):
        self.enter_to_next = is_true(value)
    def _ais_setDefaultBackground(self, value):
        pass
    def _ais_setReadOnlyBackground(self, value):
        pass
    def _ais_setPlaceHolder(self, value):
        self.placeholder = value

    def is_editable(self):
        return self.is_really_enabled() and not self.read_only
