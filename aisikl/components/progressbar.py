
from .control import Control


class ProgressBar(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.maximum = properties.get('maximum', 100)
        self.value = properties.get('value', 0)

    def _ais_setMaximum(self, value):
        self.maximum = int(value)
    def _ais_setValue(self, value):
        self.value = min(self.maximum, int(value))
