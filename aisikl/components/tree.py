# pyright: reportUninitializedInstanceVariable=none

import json
from aisikl.components.component import is_true
from aisikl.components.action import Action
from aisikl.components.control import Control
from aisikl.components.table import load_script_plain, load_script
from aisikl.events import (action_event, tree_expansion_event, tree_expansion_action_event, tree_selection_event)
from aisikl.typeutils import ct, ct_none, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag
    from collections.abc import Iterable


# Not a namedtuple, because 'expanded' and 'checked' can change.
class Node:
    def __init__(self, id: str, is_leaf: bool, type: str, expanded: bool | None, checked: bool | None, title: str) -> None:
        self.id = id
        self.is_leaf = is_leaf
        self.type = type
        self.expanded = expanded
        self.checked = checked
        self.title = title

    @override
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.__dict__!r}>'


def _synchronizer_to_cdata(sync: dict[str, bool], true_name: str, false_name: str) -> str:
    true_keys = "|".join(k for k in sync if sync[k])
    if true_keys: true_keys = "|" + true_keys + "|"
    false_keys = "|".join(k for k in sync if not sync[k])
    if false_keys: false_keys = "|" + false_keys + "|"
    return f"<{true_name}>{true_keys}</{true_name}><{false_name}>{false_keys}</{false_name}>"


class Tree(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)

        self.multiple_selection = ct(bool, properties.get('multipleSelection', False))
        self.commands = ct_none(str, properties.get('commands'))
        self.border_width = ct(int, properties.get('borderWidth', 1))
        self.action_name = ct_none(str, properties.get('an'))

        self.selection_changed = False
        self.expansion_changed = False
        self.checked_changed = False

    @override
    async def async_init(self, element: Tag | None) -> None:
        await self._init_from_data_view(nn(element).find(id=self.id + '_dataView'))

    async def _init_from_data_view(self, data_view: Tag | None, updating: bool=False) -> None:
        if not data_view: return

        element = nn(data_view.find(id='nodes'))
        selection = ct(str, element['selection'])
        self.selection = selection.split(',') if selection else []
        self.active_id = ct(str, element['activepath']) or None

        properties: dict[str, list[str]] = json.loads(nn(load_script_plain(data_view, 'json')))

        if updating:
            nodes = element
        else:
            nodes = nn(load_script(data_view, 'nodes'))
            self.nodes: dict[str, Node] = {}

        if nodes.find(nofilled=True):
            # It shouldn't be too hard to add, but we've never seen it.
            raise ValueError("noFilled attribute is not supported yet")

        for node_div in nodes.find_all(class_='nodeDiv'):
            node_element = nn(node_div.parent)

            id = ct(str, node_element['id'])
            is_leaf = node_element['isleaf'] == 'true'
            type = ct(str, node_element['type'])
            expander = node_div.find(id='nodeExpanderImage')
            expanded = ('expanded' in expander['class']) if expander else None
            checkbox = node_div.find('input', type='checkbox')
            checked = checkbox.has_attr('checked') if checkbox else None
            title = nn(node_div.find(id='nodeText')).get_text().replace('\xa0', ' ')

            self.nodes[id] = Node(id, is_leaf, type, expanded, checked, title)

        if updating:
            for id in properties['expand']:
                if not self.nodes[id].expanded:
                    await self.toggle_expansion(id, _send_event=False)
            for id in properties['collapse']:
                if self.nodes[id].expanded:
                    await self.toggle_expansion(id, _send_event=False)
        else:
            self.expansion_synchronizer: dict[str, bool] = {}
            self.checked_synchronizer: dict[str, bool] = {}

        self.dialog.try_interactive(self, "TreeSelectionEvent")

    async def _ais_setDataView(self, id: str, body: Tag) -> None:
        data_view = nn(body.find(id=id))
        if not data_view.contents: return

        if nn(data_view.find(id='nodes')).name == 'script':
            await self._init_from_data_view(data_view)
        else:
            await self._init_from_data_view(data_view, updating=True)
    _ais_setDataView.wants_body = True  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportFunctionMemberAccess]

    @override
    def changed_properties(self) -> str:
        cdata = ['<root>']

        if self.selection_changed:
            selected_paths = '|'.join(id[1:] for id in self.selection)
            cdata.append(f"<selectedPaths>{selected_paths}</selectedPaths>")
            self.selection_changed = False

        if self.active_id:
            cdata.append(f"<activePath>{self.active_id[1:]}</activePath>")

        if self.expansion_changed and self.expansion_synchronizer:
            cdata.append(_synchronizer_to_cdata(
                self.expansion_synchronizer, "expandedPaths", "collapsedPaths"))
            self.expansion_changed = False
            self.expansion_synchronizer.clear()

        if self.checked_changed and self.checked_synchronizer:
            cdata.append(_synchronizer_to_cdata(
                self.checked_synchronizer, "checkedPaths", "uncheckedPaths"))
            self.checked_changed = False
            self.checked_synchronizer.clear()

        cdata.append('</root>')

        return self._build_changed_properties(dataView=(True, True, ''.join(cdata)))

    async def double_click(self) -> None:
        await self.log('action', f'Double-clicking {self.id}')

        if self.action_name:
            action = self.dialog.components[self.action_name]
            if action:
                await ct(Action, action).execute(self.id)
                return
        ev = action_event(self, None, self.id)
        await self.dialog.app.send_events(ev)

    def _ais_setMultipleSelection(self, value: object) -> None:
        self.multiple_selection = is_true(value)
    def _ais_setCommands(self, value: object) -> None:
        self.commands = ct_none(str, value)

    async def select(self, ids: str | Iterable[str], active_id: str | None=None) -> None:
        if isinstance(ids, str):
            ids = [ids]
        else:
            ids = sorted(set(ids))

        await self.log('action',
            'Selecting ' +
            (f'node {ids[0]!r} ' if len(ids) == 1 else f'nodes {ids!r} ') +
            (f'with active id {active_id!r} ' if active_id else '') +
            f'in {self.id}')

        if not ids:
            raise ValueError('empty tree selection is not supported')

        # Pick an arbitrary active node if it doesn't matter to the caller.
        if not active_id: active_id = ids[-1]

        if len(ids) > 1 and not self.multiple_selection:
            raise ValueError('multiple selection not supported for this tree')

        self.selection = ids
        self.active_id = active_id

        self.selection_changed = True
        self.dialog.component_changes(self, False)
        ev = tree_selection_event(self, active_id, "SELECT")
        await self.dialog.app.send_events(ev)

    async def toggle_expansion(self, id: str, _send_event: bool=True) -> None:
        node = self.nodes[id]
        if node.expanded is None:
            raise ValueError("this node cannot expand")
        node.expanded = not node.expanded

        await self.log('action',
            ('Expanding ' if node.expanded else 'Collapsing ') +
            f'node {id!r} in {self.id}')

        path = id[1:]
        if self.expansion_synchronizer.get(path) == (not node.expanded):
            del self.expansion_synchronizer[path]
        elif self.expansion_synchronizer.get(path) == None:
            self.expansion_synchronizer[path] = node.expanded

            self.expansion_changed = True
            self.dialog.component_changes(self, False)

        no_filled = False   # TODO: we don't know where to look for the attribute
        if no_filled:
            ev = tree_expansion_action_event(self, path)
            await self.dialog.app.send_events(ev)

        if _send_event:
            ev = tree_expansion_event(self, path, node.expanded)
            await self.dialog.app.send_events(ev)

    async def toggle_checkbox(self, id: str) -> None:
        node = self.nodes[id]
        if node.checked is None:
            raise ValueError("this node does not have a checkbox")
        node.checked = not node.checked

        await self.log('action',
            ('Checking ' if node.checked else 'Unchecking ') +
            f'node {id!r} in {self.id}')

        path = id[1:]
        if self.checked_synchronizer.get(path) == (not node.checked):
            del self.checked_synchronizer[path]
        elif self.checked_synchronizer.get(path) == None:
            self.checked_synchronizer[path] = node.checked

            self.checked_changed = True
            self.dialog.component_changes(self, False)
            if 'CHECK_CHANGE_COMMAND|' not in (self.commands or ''): return
            self.used_listeners_mask |= 64
            ev = action_event(self, 'CHECK_CHANGE_COMMAND', self.id)
            await self.dialog.app.send_events(ev)
