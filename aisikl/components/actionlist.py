from typing import TYPE_CHECKING

from aisikl.components.component import Component
from aisikl.typeutils import ct_none

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class ActionList(Component):
    """A group of actions.

    It technically affects enabledness. Otherwise, nothing interesting.
    """

    def __init__(
        self,
        dialog: Dialog,
        id: str,
        type: str,
        parent_id: str | None,
        properties: dict[str, object],
        element: Tag | None,
    ) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        if parent_id is not None:
            raise TypeError("expected None")
        if element is not None:
            raise TypeError("expected None")
        self.owner_container_name = ct_none(
            str, properties.get("ownerContainerName"))
        self.action_ids: list[str] | None = ct_none(
            list, properties.get("actionIds"))

    @property
    def owner_container(self) -> Component | None:
        if not self.owner_container_name:
            return None
        return self.dialog.components[self.owner_container_name]
