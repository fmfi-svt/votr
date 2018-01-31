
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
    def __init__(self, source, mask_bit, xml):
        comp_name = source.id
        dlg_name = source.dialog.name

        self.source = source
        self.listening = bool(source.used_listeners_mask & mask_bit)
        self.xml = _tag('ev',
            _tag('dlgName', dlg_name) +
            ('' if comp_name == dlg_name else _tag('compName', comp_name)) +
            xml)


def _tag(name, value, optional=False):
    if optional and not value: return ''
    return '<'+name+'>' + value + '</'+name+'>'


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

def component_event(source, method, command=None):
    source.dialog.try_interactive(source, 'ComponentEvent')
    return Event(source, ComponentEventMethods[method],
        "<event class='avc.ui.event.AVCComponentEvent'>" +
        _tag("command", command, True) +
        "</event>")

# "focus" events are never sent, because webui's EventManager.createEvent()
# checks that method != "focus".
FocusEventMethods = { 'focus': 0, 'blur': EVENT_BLUR }

def focus_event(source, method, state=None):
    source.dialog.try_interactive(source, 'FocusEvent')
    return Event(source, FocusEventMethods[method],
        "<event class='avc.ui.event.AVCFocusEvent'>" +
        _tag("state", state, True) +
        "</event>")

def change_action_event(source, index=-1):
    source.dialog.try_interactive(source, 'ChangeActionEvent')
    return Event(source, EVENT_STATECHANGE,
        "<event class='avc.ui.event.AVCChangeActionEvent'>" +
        _tag("command", "CHANGE") + _tag("tabIndex", str(index)) +
        "</event>")

def cell_edited_event(source, command, alias, row_index):
    source.dialog.try_interactive(source, 'CellEditedEvent')
    return Event(source, EVENT_ACTION,
        "<event class='avc.ui.event.AVCCellEditedEvent'>" +
        _tag("command", command, True) +
        _tag("alias", alias) + _tag("rowIndex", str(row_index)) +
        "</event>")

def row_edited_event(source, command, row_index):
    source.dialog.try_interactive(source, 'RowEditedEvent')
    return Event(source, EVENT_ACTION,
        "<event class='avc.ui.event.AVCRowEditedEvent'>" +
        _tag("command", command, True) + _tag("rowIndex", str(rowIndex)) +
        "</event>")

def action_event(source, command=None, original_source_name=None,
                 params=None, cancel=False):
    source.dialog.try_interactive(source, 'ActionEvent')
    # Note that <origSrcName> goes outside of <event>.
    return Event(source, EVENT_CANCEL if cancel else EVENT_ACTION,
        _tag("origSrcName", original_source_name, True) +
        "<event class='avc.ui.event.AVCActionEvent'>" +
        _tag("command", command, True) + _tag("params", params, True) +
        "</event>")

def selection_event(source, index=-1, selected=True):
    source.dialog.try_interactive(source, 'SelectionEvent')
    return Event(source, EVENT_SELCHANGE,
        "<event class='avc.ui.event.AVCSelectionActionEvent'>" +
        _tag("command", "SELECT" if selected else "UNSELECT") +
        _tag("index", str(index)) +
        "</event>")

def tree_expansion_event(source, path, expand):
    source.dialog.try_interactive(source, 'TreeExpansionEvent')
    return Event(source, EVENT_EXPAND_COLLAPSE,
        "<event class='avc.ui.tree.AVCTreeExpansionEvent'>" +
        _tag("type", "2" if expand else "1") + _tag("path", path) +
        "</event>")

def tree_expansion_action_event(source, path):
    source.dialog.try_interactive(source, 'TreeExpansionActionEvent')
    return Event(source, EVENT_LOAD_CHILDREN,
        "<event class='avc.ui.tree.AVCTreeExpansionActionEvent'>" +
        _tag("command", "LOAD_CHILDREN") + _tag("path", path) +
        "</event>")

def tree_selection_event(source, path, command):
    source.dialog.try_interactive(source, 'TreeSelectionEvent')
    return Event(source, EVENT_TSELCHANGE,
        "<event class='avc.ui.tree.AVCTreeSelectionActionEvent'>" +
        _tag("command", command) + _tag("path", path) +
        "</event>")

CursorEventMethods = { 'pageup': EVENT_PAGEUP, 'pagedown': EVENT_PAGEDOWN }

def cursor_event(source, method, command=None):
    source.dialog.try_interactive(source, 'CursorEvent')
    return Event(source, CursorEventMethods[method],
        "<event class='avc.ui.event.AVCCursorEvent'>" +
        _tag("command", command, True) +
        "</event>")

def table_header_event(
        source, column_alias, after_column_alias, modifiers, type):
    source.dialog.try_interactive(source, 'TableHeaderEvent')
    return Event(source, EVENT_HEADER,
        "<event class='avc.ui.table.AVCTableHeaderEvent'>" +
        _tag("type", type) + _tag("columnAlias", columnAlias) +
        _tag("afterColumnAlias", afterColumnAlias, True) +
        _tag("modifiers", modifiers, True) +
        "</event>")

def item_event(source):
    source.dialog.try_interactive(source, 'ItemEvent')
    return Event(source, EVENT_ITEMCHANGE,
        "<event class='avc.ui.event.AVCItemEvent'/>")
