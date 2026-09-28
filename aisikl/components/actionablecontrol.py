from aisikl.components.action import Action
from aisikl.components.actionlist import ActionList
from aisikl.components.control import Control
from aisikl.typeutils import ct, ct_none
from aisikl.operations import Operations
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class ActionableControl(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.action_name = ct_none(str, properties.get('an'))

    @property
    def action(self) -> Action | None:
        if not self.action_name: return None
        return ct(Action, self.dialog.components[self.action_name])

    async def try_execute_action(self, *, params: str | None = None, return_ops: bool) -> tuple[bool, Operations]:
        if self.action:
            ops = await self.action.execute(
                self.id, params, return_ops=return_ops)
            return (True, ops)
        return (False, Operations())

    @override
    def is_really_enabled(self) -> bool:
        return (super().is_really_enabled() and
                self.get_enabled_by_owner_container())

    def get_enabled_by_owner_container(self) -> bool:
        action = self.action
        if not action: return True
        action_list = action.get_action_list()
        if not action_list: return True
        owner_container = ct(ActionList, action_list).owner_container
        if not owner_container: return True
        return owner_container.is_really_enabled()
