# pyright: reportUninitializedInstanceVariable=none

import json
import re
from typing import TYPE_CHECKING, Literal, override

from aisikl.components import component_classes
from aisikl.components.control import Control
from aisikl.events import component_event
from aisikl.exceptions import AISParseError
from aisikl.typeutils import ct, nn

if TYPE_CHECKING:
    from aisikl.app import Application
    from aisikl.components.component import Component
    from aisikl.operations import Operations

_properties_re = re.compile(r"^var componentsProperties\s*=\s*(.*);$")

class Dialog:
    """An artificial "window within a window" in the AIS UI.

    Each [`Application`][] (real browser window) contains one main dialog and
    zero or more floating dialogs rendered above it.

    Dialogs consist of *components*: widgets like buttons, tables, etc. You can
    access them either as dialog attributes with ``d.foobarButton``, or as dict
    items with ``d.components["foobarButton"]``. The component list is
    dynamically populated based on the AIS server's response.

    webui.js code also uses the term "dialog" for "native dialogs" -- message
    boxes, confirm boxes, abort boxes, etc. In Votr, ``Dialog`` is only used for
    real component-based dialogs.

    Tip:
        Component IDs are assigned by AIS developers. Since they are considered
        an internal detail, they often make even less sense than the visible
        parts. When you as a developer see a component in the real AIS UI, you
        have two ways to discover its ID:

        1.  Ctrl+Alt+Shift+left-click the component to show its ID. Beware that
            it still counts as a click (e.g. a clicked button is activated).
        2.  Open developer tools, press inspect element, and click on the object
            of interest. Then keep pressing the left arrow key until you find
            the right ancestor (e.g. from a table cell to the root of the entire
            table), and read its `id=""`.
    """

    def __init__(self, name: str, title: str, code: str, parent_dialog_name: str | None, modal: bool,
                 is_main_dialog: bool, closeable: bool, hide_title_bar: bool, app: Application[object]) -> None:
        """Internal."""
        self.name = name
        """Dialog instance ID dynamically assigned by the AIS server.

        Example: "VSES007_StudentZoznamPrihlaseniNaSkuskuDlg0".
        """

        self.title = title
        """User-visible dialog title."""

        self.code = code
        """Alphanumeric code identifying the dialog type.

        - Example: "VSES007".
        - The original AIS UI displays it in the top right corner.
        - The main dialog's code is equal to the application ID.
        - May be an empty string, e.g. in the table column settings dialog.
        """

        self.parent_dialog_name = parent_dialog_name
        """Parent dialog ID, if any.

        Empirically, it's ``None`` *iff* [`modal`][] is false.
        """

        self.modal = modal
        """Whether it blocks interaction with other dialogs when it's open.

        Empirically, it's true *iff* [`is_main_dialog`][] is false.
        webui.js theoretically contains code for non-main non-modal dialogs,
        but we've never seen any.
        """

        self.is_main_dialog = is_main_dialog
        """Whether it contains the application's base UI."""

        self.closeable = closeable
        """Whether it has a close button.

        Empirically, it's always true -- even for main dialogs, which don't have
        a close button in the AIS UI.
        """

        self.hide_title_bar = hide_title_bar
        """Whether the title bar is invisible.

        Empirically, it's always false -- even for main dialogs, which don't
        have a title bar in the AIS UI.
        """

        self.app = app
        """The [`Application`][] this dialog belongs to."""

        self.components: dict[str, Component] = {}
        """Dict of the dialog's components, keyed by component ID."""

        self._changed_components: dict[str, Literal[True]] | None = None
        """Internal. Tracks components whose state has changed since the last
        request was sent.
        """

    async def init(self, url: str) -> None:
        """Internal. Retrieves and parses the HTML page with the dialog's body.

        Called from [`aisikl.operations.OpenDialogOp.perform`][] and
        [`aisikl.operations.RefreshDialogOp.perform`][].
        """
        dialog_soup = await self.app.ctx.parse_html(
            await self.app.ctx.request_ais(url))
        await self.app.ctx.log("benchmark", "Begin dialog initialization")

        body = nn(dialog_soup.body)
        first_element_child = body.find(True)
        scripts = dialog_soup.find_all("script")
        if not (body.get("id") == self.name and
                "jsct" not in body and
                "dialogBody" in (body.get("class") or []) and
                first_element_child and
                first_element_child.get("id") == "dialogComponentsArea" and
                scripts):
            raise AISParseError("Unexpected dialog body response")

        self.components = {}
        self._changed_components = None

        last_line = nn(scripts[-1].string).strip().split("\n")[-1].strip()
        match = _properties_re.match(last_line)
        if not match:
            raise AISParseError("Couldn't find dialog componentProperties")
        component_properties: dict[str, dict[str, object]] = json.loads(match.group(1))

        elements = { e["id"]: e for e in dialog_soup.find_all(id=True) }
        if "dt_selection" in elements or "dt_selection_area" in elements:
            raise AISParseError("#dt_selection is not supported")

        for id, properties in component_properties.items():
            if properties.get("tmp"): continue
            if id == "suggestionsArea": continue

            element = elements.get(id)
            parent_id = None
            if element:
                parent = element.find_parent(
                    lambda p: p.get("id") in component_properties)
                if parent:
                    parent_id = ct(str, parent["id"])

            type = ct(str, properties.get("t"))
            if type not in component_classes:
                raise AISParseError(f"Unsupported component type: {type!r}")
            component = component_classes[type](
                self, id, type, parent_id, properties, element)
            await component.async_init(element)

            self.components[id] = component

        self.body = self.components[self.name]

        await self.app.ctx.log("benchmark", "End dialog initialization")

    if not TYPE_CHECKING:
        def __getattr__(self, name: str) -> Component:
            """Accesses the dialog's components as attributes."""
            if "components" in self.__dict__ and name in self.components:
                return self.components[name]
            raise AttributeError(name)

    @override
    def __dir__(self) -> list[str]:
        """Lists components. Used in IPython's auto-completion."""
        return [*super().__dir__(), *self.components]

    def changed_properties(self) -> str:
        """Internal. Builds the ``<changedProperties>`` string for this dialog
        and resets marked changes. Partially corresponds to
        ``WebUI.changesToXML`` in webui.js.
        """
        # We ignore width, height, x, y, focusedComponent and dtSelection.
        # So there are no <nameValue> pairs, only <embObjChProps>.
        if self._changed_components is None: return ""
        result = (
            f"<changedProperties><objName>{self.name}</objName>\n" +
            "<embObjChProps>\n" +
            "".join(ct(Control, self.components[id]).changed_properties()
                    for id in self._changed_components) +
            "</embObjChProps>\n" +
            "</changedProperties>\n")
        self._changed_components = None
        return result

    def try_interactive(self, component: Component, type: str) -> None:
        """Internal. Corresponds to ``DialogBody.tryInteractive`` in webui.js,
        but it's not yet implemented.
        """
        pass # TODO

    def component_changes(self, component: Control, is_minor: bool) -> None:
        """Internal. Marks a component as changed. Corresponds to
        ``DialogBody.componentChanges`` in webui.js.
        """
        # TODO: Eventual support for ChangeGuardInteractive goes here.
        # (is_minor decides whether to set elementsChanged or not.)

        if self._changed_components is None:
            # Use dict instead of set as it has consistent iteration order in
            # Python 3.7+, unlike set. (https://stackoverflow.com/q/3848091)
            # The server seems to accept any order, but being deterministic is
            # occasionally handy when inspecting or comparing log files.
            #
            # In theory _changed_components == {} means only the dialog itself
            # has changed, and None means no change at all. But Votr ignores
            # Dialog properties, and never calls component_changes(None, ...).
            self._changed_components = {}

        if component:
            self._changed_components[component.id] = True
            self.try_interactive(component, "change")

    async def click_close_button(self, *, return_ops: Literal[True]) -> Operations:
        """Clicks the close button.

        AIS usually responds with one
        [`CloseDialogOp`][aisikl.operations.CloseDialogOp].

        Many dialogs also have a normal button component named ``closeButton``.
        In practice, they usually do the same thing.
        """
        if self.is_main_dialog or not self.closeable:
            raise ValueError(f"Dialog {self.name} has no close button")
        # TODO: Return unless "self.enabled" is True.

        await self.app.ctx.log("action",
            f"Pressing close button of {self.name}")
        ev = component_event(self.body, "close", "CLOSE")
        return await self.app.send_events(ev, return_ops=return_ops)
