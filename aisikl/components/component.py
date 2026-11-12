from typing import TYPE_CHECKING

from aisikl.exceptions import AISParseError
from aisikl.typeutils import ct, ct_none, really_int

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog


def is_true(value: object) -> bool:
    """Internal. Parses the AIS server's boolean values in component ``_ais_*``
    setter methods. Corresponds to the many webui.js setter methods that call
    ``cmn_toBoolean`` or compute ``value == true || value == "true"``.
    """
    # Let's not actually do `value == true || value == "true"`.
    # This JavaScript expression allows even 1, "1", [1] because it uses `==`.
    # But empirically, the AIS server always emits "true" and "false" strings.
    # `value == true` is probably only for setter calls within webui.js itself.
    # (This can be relaxed if needed later.)
    if value == "true":
        return True
    if value == "false":
        return False
    raise TypeError(f"Expected 'true' or 'false' string, not {value!r}")


class Component:
    """Base class for WebUI components.

    For the most part, tangible component types (e.g. buttons, tables) inherit
    from ``Component``'s subclass [`Control`][aisikl.components.control.Control]
    and intangible component types (e.g. actions, action lists) inherit directly
    from ``Component``.

    In webui.js, ``Component`` technically has a parent class -- ``JSObject``,
    but in Aisikl both are merged into ``Component``.
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
        """Internal."""
        self.dialog = dialog
        self.id = id
        self.component_type = type
        self.used_listeners_mask = ct(int, properties.get("ulm", 0))
        self.enabled = ct(bool, properties.get("e", True))
        self.enabled_in_ui = ct(bool, properties.get("enabledInUI", True))
        self.visible = ct(bool, properties.get("v", True))
        self.visible_in_ui = ct(bool, properties.get("visibleInUI", True))
        self.title = ct_none(str, properties.get("title"))
        self.popup_menu = ct_none(str, properties.get("pm"))

        if properties.get("state", 1) == 2:
            raise AISParseError("STATE_DT is not supported")

    async def async_init(self, element: Tag | None) -> None:
        """Internal."""
        pass

    async def log(
        self, type: str, message: str, data: object = None, /
    ) -> None:
        """Internal. Calls [`Context.log`][aisikl.context.Context.log] to log a
        message. Convenience helper to allow shorter log calls.
        """
        await self.dialog.app.ctx.log(type, message, data)

    def is_really_enabled(self) -> bool:
        """Returns whether this component would be enabled in the AIS UI.

        Because ``ValueInteractive`` and related objects are not yet implemented
        in Aisikl, the result is only approximate. It might not always perfectly
        match what you'd get in the AIS UI.

        Due to the above, Aisikl allows you to interact with components even if
        they're disabled. The usual result is that the AIS server ignores the
        event (returning no [`Operations`][aisikl.operations.Operations]). You
        can call ``is_really_enabled`` to predict this in advance.

        Corresponds to ``realizeEnability`` in webui.js, but as a getter.
        """
        return self.enabled and self.enabled_in_ui

    def _ais_setState(self, value: object) -> None:
        if really_int(value) == 2:
            raise AISParseError("STATE_DT is not supported")

    def _ais_setUsedListenersMask(self, value: object) -> None:
        self.used_listeners_mask = really_int(value)

    def _ais_setEnabled(self, value: object) -> None:
        self.enabled = is_true(value)

    def _ais_setEnabledInUI(self, value: object) -> None:
        self.enabled_in_ui = is_true(value)

    def _ais_setVisible(self, value: object) -> None:
        self.visible = is_true(value)

    def _ais_setVisibleInUI(self, value: object) -> None:
        self.visible_in_ui = is_true(value)

    def _ais_setTitle(self, value: object) -> None:
        self.title = ct_none(str, value)

    def _ais_setPopupMenu(self, value: object) -> None:
        self.popup_menu = ct_none(str, value)
