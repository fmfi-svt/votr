
from .component import Component


class ActionList(Component):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.owner_container_name = properties.get('ownerContainerName')
        self.action_ids = properties.get('actionIds')

    @property
    def owner_container(self):
        if not self.owner_container_name: return None
        return self.dialog.components[self.owner_container_name]
