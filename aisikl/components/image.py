
from .control import Control


class Image(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.image = element.img.get('src', '')

    def _ais_setImage(self, value):
        self.image = '/ais/images/' + value + '.png'
    def _ais_setUrl(self, value):
        self.image = value
