from typing import TYPE_CHECKING, override

from aisikl.components.action import Action
from aisikl.components.control import Control
from aisikl.operations import Operations
from aisikl.typeutils import ct, ct_none

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class ActionableControl(Control):
    """Abstract base class for controls that can trigger an [`Action`][] (except
    [`Table`][aisikl.components.table.Table] and
    [`Tree`][aisikl.components.tree.Tree], for some reason).
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
        self.action_name = ct_none(str, properties.get("an"))

    @property
    def action(self) -> Action | None:
        if not self.action_name:
            return None
        return ct(Action, self.dialog.components[self.action_name])

    async def _try_execute_action(
        self, *, params: str | None = None, return_ops: bool
    ) -> tuple[bool, Operations]:
        """Internal. Executes the component's action, if it has one.

        Returns:
            did: Whether an action was executed.
            ops: What operations happened.
        """
        if self.action:
            ops = await self.action.execute(
                self.id, params, return_ops=return_ops)
            return (True, ops)
        return (False, Operations())

    @override
    def is_really_enabled(self) -> bool:
        return (
            super().is_really_enabled()
            and self._get_enabled_by_owner_container()
        )

    def _get_enabled_by_owner_container(self) -> bool:
        """Internal. Corresponds to ``getEnabledByOwnerContainer`` in
        webui.js.
        """
        action = self.action
        if not action:
            return True
        action_list = action.get_action_list()
        if not action_list:
            return True
        owner_container = action_list.owner_container
        if not owner_container:
            return True
        return owner_container.is_really_enabled()
