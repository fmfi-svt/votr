
from .control import Control


class StackedPane(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.title = element.get('name')
