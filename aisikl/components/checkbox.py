from typing import TYPE_CHECKING, override

from aisikl.components.component import is_true
from aisikl.components.control import Control
from aisikl.events import item_event
from aisikl.operations import Operations
from aisikl.typeutils import ct_none, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


class CheckBox(Control):
    """A WebUI checkbox."""

    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        # We only ever saw shortcut==None, but webui calls toUpperCase().
        self.shortcut = ct_none(str, properties.get("sc"))
        """Key shortcut, probably. Empirically, it's always ``None``."""
        input = nn(nn(element).input)
        self.smoked = input.get("smoked", "false") == "true"
        """Whether it's in an "indeterminate" AKA "partially checked" state."""
        self.selected = input.has_attr("checked")
        """Whether it's checked."""

    def _ais_setSmoked(self, value: object) -> None:
        self.smoked = is_true(value)
    def _ais_setSelected(self, value: object) -> None:
        self.selected = is_true(value)
        self.dialog.try_interactive(self, "ItemEvent")

    async def _fire_event(self, *, return_ops: bool) -> Operations:
        self.dialog.component_changes(self, False)
        ev = item_event(self)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    @override
    def changed_properties(self) -> str:
        return self._build_changed_properties(
            selected=self.selected, smoked=self.smoked)

    async def toggle(self, *, return_ops: bool = False) -> Operations:
        """Checks or unchecks the checkbox."""
        self.selected = not self.selected
        self.smoked = False
        log_verb = "Checking" if self.selected else "Unchecking"
        await self.log("action", f"{log_verb} {self.id}")
        return await self._fire_event(return_ops=return_ops)

    async def set_to(self, value: bool, *, return_ops: bool = False) -> Operations:
        """Sets the checkbox to ``value`` if it's not already there."""
        if self.smoked or self.selected != bool(value):
            self.selected = bool(value)
            self.smoked = False
            log_verb = "Checking" if self.selected else "Unchecking"
            await self.log("action", f"{log_verb} {self.id}")
            return await self._fire_event(return_ops=return_ops)
        else:
            return Operations()
