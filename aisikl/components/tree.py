
import json
from .component import is_true
from .control import Control
from .table import load_script_plain, load_script
from aisikl.events import (action_event, tree_expansion_event,
                           tree_expansion_action_event, tree_selection_event)


# Not a namedtuple, because 'expanded' and 'checked' can change.
class Node(object):
    def __init__(self, id, is_leaf, type, expanded, checked, title):
        self.id = id
        self.is_leaf = is_leaf
        self.type = type
        self.expanded = expanded
        self.checked = checked
        self.title = title

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, repr(self.__dict__))


def _synchronizer_to_cdata(sync, true_name, false_name):
    true_keys = "|".join(k for k in sync if sync[k])
    if true_keys: true_keys = "|" + true_keys + "|"
    false_keys = "|".join(k for k in sync if not sync[k])
    if false_keys: false_keys = "|" + false_keys + "|"
    return "<{}>{}</{}><{}>{}</{}>".format(
        true_name, true_keys, true_name, false_name, false_keys, false_name)


class Tree(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)

        self.multiple_selection = properties.get('multipleSelection', False)
        self.commands = properties.get('commands')
        self.border_width = properties.get('borderWidth', 1)
        self.action_name = properties.get('an')

        self.selection_changed = False
        self.expansion_changed = False
        self.checked_changed = False

        self._init_from_data_view(element.find(id=self.id + '_dataView'))

    def _init_from_data_view(self, data_view, updating=False):
        if not data_view: return

        element = data_view.find(id='nodes')
        selection = element.get('selection')
        self.selection = selection.split(',') if selection else []
        self.active_id = element.get('activepath') or None

        properties = json.loads(load_script_plain(data_view, 'json'))

        if updating:
            nodes = element
        else:
            nodes = load_script(data_view, 'nodes')
            self.nodes = {}

        if nodes.find(nofilled=True):
            # It shouldn't be too hard to add, but we've never seen it.
            raise ValueError("noFilled attribute is not supported yet")

        for node_div in nodes.find_all(class_='nodeDiv'):
            node_element = node_div.parent

            id = node_element['id']
            is_leaf = node_element['isleaf'] == 'true'
            type = node_element['type']
            expander = node_div.find(id='nodeExpanderImage')
            expanded = ('expanded' in expander['class']) if expander else None
            checkbox = node_div.find('input', type='checkbox')
            checked = checkbox.has_attr('checked') if checkbox else None
            title = node_div.find(id='nodeText').get_text().replace('\xa0', ' ')

            self.nodes[id] = Node(id, is_leaf, type, expanded, checked, title)

        if updating:
            for id in properties['expand']:
                if not self.nodes[id].expanded:
                    self.toggle_expansion(id, _send_event=False)
            for id in properties['collapse']:
                if self.nodes[id].expanded:
                    self.toggle_expansion(id, _send_event=False)
        else:
            self.expansion_synchronizer = {}
            self.checked_synchronizer = {}

        self.dialog.try_interactive(self, "TreeSelectionEvent")

    def _ais_setDataView(self, id, body):
        data_view = body.find(id=id)
        if not data_view.contents: return

        if data_view.find(id='nodes').name == 'script':
            self._init_from_data_view(data_view)
        else:
            self._init_from_data_view(data_view, updating=True)
    _ais_setDataView.wants_body = True

    def changed_properties(self):
        cdata = ['<root>']

        if self.selection_changed:
            selected_paths = '|'.join(id[1:] for id in self.selection)
            cdata.append("<selectedPaths>{}</selectedPaths>".format(selected_paths))
            self.selection_changed = False

        active_path = self.active_id[1:]
        if active_path:
            cdata.append("<activePath>{}</activePath>".format(active_path))

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

    def double_click(self):
        if self.action_name:
            action = self.dialog.components[self.action_name]
            if action:
                action.on_execute(self.id)
                return
        ev = action_event(self, None, self.id)
        self.dialog.app.send_events(ev)

    def _ais_setMultipleSelection(self, value):
        self.multiple_selection = is_true(value)
    def _ais_setCommands(self, value):
        self.commands = value

    def select(self, ids, active_id=None):
        if isinstance(ids, str):
            ids = [ids]
        else:
            ids = sorted(set(ids))

        if not ids:
            raise ValueError('empty tree selection is not supported')

        # Pick an arbitrary active node if it doesn't matter to the caller.
        if active_id is None: active_id = ids[-1]

        if len(ids) > 1 and not self.multiple_selection:
            raise ValueError('multiple selection not supported for this tree')

        self.selection = ids
        self.active_id = active_id

        self.selection_changed = True
        self.dialog.component_changes(self, False)
        ev = tree_selection_event(self, active_id, "SELECT")
        self.dialog.app.send_events(ev)

    def toggle_expansion(self, id, _send_event=True):
        node = self.nodes[id]
        if node.expanded is None:
            raise ValueError("this node cannot expand")
        node.expanded = not node.expanded

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
            self.dialog.app.send_events(ev)

        if _send_event:
            ev = tree_expansion_event(self, path, node.expanded)
            self.dialog.app.send_events(ev)

    def toggle_checkbox(self, id):
        node = self.nodes[id]
        if node.checked is None:
            raise ValueError("this node does not have a checkbox")
        node.checked = not node.checked

        path = id[1:]
        if self.checked_synchronizer.get(path) == (not node.checked):
            del self.checked_synchronizer[path]
        elif self.checked_synchronizer.get(path) == None:
            self.checked_synchronizer[path] = node.checked

            self.checked_changed = True
            self.dialog.component_changes(self, False)
            if 'CHECK_CHANGE_COMMAND|' not in self.commands: return
            self.used_listeners_mask |= 64
            ev = action_event(self, 'CHECK_CHANGE_COMMAND', self.id)
            self.dialog.app.send_events(ev)
