
from aisikl.exceptions import AISParseError
from .base import Component


class DialogBody(Component):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)

        if (element.find(id='dt_selection') or
            element.find(id='dt_selection_area')):
            raise AISParseError("#dt_selection is not supported")

        # TODO: See if anything else needs to be done when initializing
        # DialogBody. (popupMenuManager?) Try to avoid dealing with focus.

        # TODO: Seeing as this class does so little, consider just using
        # Component for jsct="body" and moving the rest to Dialog.__init__().
