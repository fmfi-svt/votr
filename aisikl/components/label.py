
from .control import Control


class Label(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.title_like_text = element.get('titleliketext')
        self.for_ = element.get('for')
        self.text = element.get_text()

    def _ais_setTitleLikeText(self, value):
        self.title_like_text = value
    def _ais_setFor(self, value):
        self.for_ = value

    def _ais_setImage(self, value):
        self.image = '/ais/images/' + value + '.png'
    def _ais_setUrl(self, value):
        self.image = value
