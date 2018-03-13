
from .control import Control


class Image(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.image = element.img.get('src', '')

    def _ais_setImage(self, value):
        self.image = '/ais/images/' + value + '.png'
    def _ais_setUrl(self, value):
        self.image = value
