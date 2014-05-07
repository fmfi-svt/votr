
from .control import Control


class ProgressBar(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.maximum = int(element.get('maximum', '100'))
        self.value = int(element.get('value', '0'))

    def _ais_setMaximum(self, value):
        self.maximum = int(value)
    def _ais_setValue(self, value):
        self.value = min(self.maximum, int(value))
