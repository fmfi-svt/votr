
from collections import namedtuple
from aisikl.components.control import Control
from aisikl.events import selection_event
from aisikl.exceptions import AmbiguousItemError, NotFoundError


Option = namedtuple('Option', ['title', 'id', 'tool_tip_text'])


class ComboBox(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.tool_tip_like_data = properties.get('ttld', False)
        self._parse_options(element)

    def _parse_options(self, element):
        self.selected_index = -1
        self.options = []
        for index, option in enumerate(element.find_all('option')):
            self.options.append(Option(
                title=option.get_text(),
                id=option.get('sid', ''),
                tool_tip_text=option.get('title', ''),
            ))
            if option.has_attr('selected'):
                self.selected_index = index

    @property
    def selected_option(self):
        if self.selected_index == -1: return None
        return self.options[self.selected_index]

    def select(self, index):
        self.log('action', 'Selecting "{}" in {}'.format(
            self.options[index].title, self.id))
        self.selected_index = index
        self._fire_event()

    def _select_by_attr(self, name, value, unless_selected):
        matches = [i for i, option in enumerate(self.options) if getattr(option, name) == value]
        if not matches:
            raise NotFoundError("Combo box option with {} = {!r} not found".format(name, value))
        if len(matches) > 1:
            raise AmbiguousItemError("Multiple combo box options have {} = {!r}".format(name, value))

        if unless_selected and self.selected_index == matches[0]:
            return False
        else:
            self.select(matches[0])
            return True

    def select_by_id(self, id, *, unless_selected=False):
        # I'm not sure if unless_selected=False is the best default, but that's
        # how the code worked before I added this helper function...
        return self._select_by_attr('id', id, unless_selected)

    def select_by_title(self, title, *, unless_selected=False):
        return self._select_by_attr('title', title, unless_selected)

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        ev = selection_event(self, self.selected_index)
        self.dialog.app.send_events(ev)

    def changed_properties(self):
        cdata = ('<root><selection>'
            '<selectedIndexes>{}</selectedIndexes>'
            '</selection></root>').format(self.selected_index)
        return self._build_changed_properties(dataView=(True, True, cdata))

    def _ais_setDataView(self, id, body):
        data_view = body.find(id=id)
        combo_box_list = data_view.find(id='comboBoxList', recursive=False)
        if combo_box_list.has_attr('selectedIndex_'):
            self.selected_index = int(combo_box_list['selectedIndex_'])
        else:
            self._parse_options(combo_box_list)
        self.dialog.try_interactive(self, 'SelectionEvent')
    _ais_setDataView.wants_body = True
