
from __future__ import annotations
from .component import Component
from typing import TYPE_CHECKING, Dict, List, Union

if TYPE_CHECKING:
    from aisikl.dialog import Dialog


class ActionList(Component):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: None, properties: Dict[str, Union[str, List[str]]], element: None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.owner_container_name = properties.get('ownerContainerName')
        self.action_ids = properties.get('actionIds')

    @property
    def owner_container(self):
        if not self.owner_container_name: return None
        return self.dialog.components[self.owner_container_name]
