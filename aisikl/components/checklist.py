
from .component import is_true
from .control import Control


# Not a namedtuple, because 'checked' can change.
class Item:
    def __init__(self, title, id, sid, rid, tool_tip_text, checked):
        self.title = title
        self.id = id
        self.sid = sid
        self.rid = rid
        self.tool_tip_text = tool_tip_text
        self.checked = checked

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, repr(self.__dict__))


class CheckList(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_down_enabled = properties.get('upDownEnabled', False)
        self._parse_items(element)

    def _parse_items(self, element):
        self.selected_index = -1
        self.items = []
        for index, tr in enumerate(element.find_all('tr')):
            td = tr.td
            self.items.append(Item(
                title=tr.get_text(),
                id=td['id'], sid=tr['sid'], rid=tr['rid'],
                tool_tip_text=td['title'],
                checked=tr.input.has_attr('checked'),
            ))
            if 'selectedListRow' in tr.get('class', []):
                self.selected_index = index

    def up_down_row(self, command):
        raise Exception('up_down_row not yet implemented.')   # TODO

    def select_unselect_all(self):
        if not self.items: return
        new_value = not self.items[0].checked
        self.log('action', '{} all items in {}'.format(
            'Selecting' if new_value else 'Unselecting', self.id))
        for item in self.items:
            item.checked = new_value
        self._mark_changed()

    def select(self, index):
        self.log('action', 'Selecting item "{}" {}'.format(
            self.items[index].title, self.id))
        self.selected_index = index

    def toggle(self, index):
        self.items[index].checked = not self.items[index].checked
        self.log('action', '{} item "{}" in {}'.format(
            'Checking' if self.items[index].checked else 'Unchecking',
            self.items[index].title, self.id))
        self.selected_index = index
        self._mark_changed()

    def _ais_setUpDownEnabled(self, value):
        self.up_down_enabled = is_true(value)
    def _ais_setDataView(self, id, body):
        self._parse_items(body.find(id=id))
    _ais_setDataView.wants_body = True

    def _mark_changed(self):
        self.dialog.component_changes(self, False)

    def changed_properties(self):
        selection = ','.join(
            ('' if item.checked else '-') + item.rid for item in self.items)

        for index, item in enumerate(self.items):
            item.rid = str(index)

        cdata = ('<root><selection>'
            '<selectedIndexes>{}</selectedIndexes>'
            '</selection></root>').format(selection)
        return self._build_changed_properties(dataView=(True, True, cdata))
