
from .component import Component


class ActionList(Component):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.owner_container_name = element.get('ownercontainername')

    @property
    def owner_container(self):
        if not self.owner_container_name: return None
        return self.dialog.components[self.owner_container_name]
