
from .control import Control


class StackedPane(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.title = element.get('name')
