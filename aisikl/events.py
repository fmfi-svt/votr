from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.components.component import Component


class Event:
    '''A WebUI event that might be sent to the server.

    Events should be created using the functions below instead of using the
    constructor directly.

    Attributes:
        source: The component that fired the event.
        listening: Whether the server actually wants the event. If false,
            :meth:`aisikl.app.Application.send_events` will ignore it.
        xml: The XML payload.
    '''
    def __init__(self, source: Component, mask_bit: int, xml: str) -> None:
        comp_name = source.id
        dlg_name = source.dialog.name

        self.source = source
        self.listening = bool(source.used_listeners_mask & mask_bit)
        self.xml = _tag('ev',
            _tag('dlgName', dlg_name) +
            ('' if comp_name == dlg_name else _tag('compName', comp_name)) +
            xml)


def _tag(name: str, value: str) -> str:
    return '<'+name+'>' + value + '</'+name+'>'

def _maybetag(name: str, value: str | None) -> str:
    if not value: return ''
    return _tag(name, value)


EVENT_INIT = 1
EVENT_CLOSE = 2
EVENT_FOCUS = 4
EVENT_BLUR = 8
EVENT_STATECHANGE = 32
EVENT_ACTION = 64
EVENT_SELCHANGE = 128
EVENT_EXPAND_COLLAPSE = 256
EVENT_LOAD_CHILDREN = 512
EVENT_TSELCHANGE = 1024
EVENT_PAGEUP = 2048
EVENT_PAGEDOWN = 4096
EVENT_HEADER = 8192
EVENT_ITEMCHANGE = 16384
EVENT_BEFORECLOSE = 65536
EVENT_CANCEL = 131072


ComponentEventMethods = {
    'init': EVENT_INIT,
    'close': EVENT_CLOSE,
    'beforeclose': EVENT_BEFORECLOSE
}

def component_event(source: Component, method: str, command: str | None=None) -> Event:
    source.dialog.try_interactive(source, 'ComponentEvent')
    return Event(source, ComponentEventMethods[method],
        "<event class='avc.ui.event.AVCComponentEvent'>" +
        _maybetag("command", command) +
        "</event>")

# "focus" events are never sent, because webui's EventManager.createEvent()
# checks that method != "focus".
FocusEventMethods = { 'focus': 0, 'blur': EVENT_BLUR }

def focus_event(source: Component, method: str, state: str | None=None) -> Event:
    source.dialog.try_interactive(source, 'FocusEvent')
    return Event(source, FocusEventMethods[method],
        "<event class='avc.ui.event.AVCFocusEvent'>" +
        _maybetag("state", state) +
        "</event>")

def change_action_event(source: Component, index: int=-1) -> Event:
    source.dialog.try_interactive(source, 'ChangeActionEvent')
    return Event(source, EVENT_STATECHANGE,
        "<event class='avc.ui.event.AVCChangeActionEvent'>" +
        _tag("command", "CHANGE") + _tag("tabIndex", str(index)) +
        "</event>")

def cell_edited_event(source: Component, command: str, alias: str, row_index: int) -> Event:
    source.dialog.try_interactive(source, 'CellEditedEvent')
    return Event(source, EVENT_ACTION,
        "<event class='avc.ui.event.AVCCellEditedEvent'>" +
        _maybetag("command", command) +
        _tag("alias", alias) + _tag("rowIndex", str(row_index)) +
        "</event>")

def row_edited_event(source: Component, command: str, row_index: int) -> Event:
    source.dialog.try_interactive(source, 'RowEditedEvent')
    return Event(source, EVENT_ACTION,
        "<event class='avc.ui.event.AVCRowEditedEvent'>" +
        _maybetag("command", command) + _tag("rowIndex", str(row_index)) +
        "</event>")

def action_event(source: Component, command: str | None=None, original_source_name: str | None=None,
                 params: str | None=None, cancel: bool=False) -> Event:
    source.dialog.try_interactive(source, 'ActionEvent')
    # Note that <origSrcName> goes outside of <event>.
    return Event(source, EVENT_CANCEL if cancel else EVENT_ACTION,
        _maybetag("origSrcName", original_source_name) +
        "<event class='avc.ui.event.AVCActionEvent'>" +
        _maybetag("command", command) +
        (f"<params><![CDATA[{params}]]></params>" if params else "") +
        "</event>")

def selection_event(source: Component, index: int=-1, selected: bool=True) -> Event:
    source.dialog.try_interactive(source, 'SelectionEvent')
    return Event(source, EVENT_SELCHANGE,
        "<event class='avc.ui.event.AVCSelectionActionEvent'>" +
        _tag("command", "SELECT" if selected else "UNSELECT") +
        _tag("index", str(index)) +
        "</event>")

def tree_expansion_event(source: Component, path: str, expand: bool) -> Event:
    source.dialog.try_interactive(source, 'TreeExpansionEvent')
    return Event(source, EVENT_EXPAND_COLLAPSE,
        "<event class='avc.ui.tree.AVCTreeExpansionEvent'>" +
        _tag("type", "2" if expand else "1") + _tag("path", path) +
        _tag("fromViewer", "true") +
        "</event>")

def tree_expansion_action_event(source: Component, path: str) -> Event:
    source.dialog.try_interactive(source, 'TreeExpansionActionEvent')
    return Event(source, EVENT_LOAD_CHILDREN,
        "<event class='avc.ui.tree.AVCTreeExpansionActionEvent'>" +
        _tag("command", "LOAD_CHILDREN") + _tag("path", path) +
        "</event>")

def tree_selection_event(source: Component, path: str, command: str) -> Event:
    source.dialog.try_interactive(source, 'TreeSelectionEvent')
    return Event(source, EVENT_TSELCHANGE,
        "<event class='avc.ui.tree.AVCTreeSelectionActionEvent'>" +
        _tag("command", command) + _tag("path", path) +
        "</event>")

CursorEventMethods = { 'pageup': EVENT_PAGEUP, 'pagedown': EVENT_PAGEDOWN }

def cursor_event(source: Component, method: str, command: str | None=None) -> Event:
    source.dialog.try_interactive(source, 'CursorEvent')
    return Event(source, CursorEventMethods[method],
        "<event class='avc.ui.event.AVCCursorEvent'>" +
        _maybetag("command", command) +
        "</event>")

def table_header_event(
        source: Component, column_alias: str, after_column_alias: str | None, modifiers: str | None, type: str) -> Event:
    source.dialog.try_interactive(source, 'TableHeaderEvent')
    return Event(source, EVENT_HEADER,
        "<event class='avc.ui.table.AVCTableHeaderEvent'>" +
        _tag("type", type) + _tag("columnAlias", column_alias) +
        _maybetag("afterColumnAlias", after_column_alias) +
        _maybetag("modifiers", modifiers) +
        "</event>")

def item_event(source: Component) -> Event:
    source.dialog.try_interactive(source, 'ItemEvent')
    return Event(source, EVENT_ITEMCHANGE,
        "<event class='avc.ui.event.AVCItemEvent'/>")
