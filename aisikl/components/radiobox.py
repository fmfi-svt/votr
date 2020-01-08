
from collections import namedtuple
from .control import Control
from aisikl.events import selection_event
from aisikl.exceptions import AISParseError


Option = namedtuple('Option', ['title', 'id'])


class RadioBox(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)

        items = element.find(id='radioBox_items')
        self.always_selected = items.get('allwaysselected', 'false') == 'true'

        self._parse_options(items)

    def _parse_options(self, items):
        self.selected_index = -1
        self.options = []
        for index, td in enumerate(items.find_all('td')):
            if self.enabled and td['index'] != str(index):
                raise AISParseError(
                    "RadioBox '{}' item #{} "
                    "has unexpected index attribute.".format(self.id, index))
            self.options.append(Option(
                title=td.label.get_text(),
                id=td.input.get('sid'),
            ))
            if td.input.has_attr('checked'):
                self.selected_index = index

    @property
    def selected_option():
        if self.selected_index == -1: return None
        return self.options[self.selected_index]

    # If self.always_selected == False, select(-1) unselects the current item.
    # (Votr always allows select(-1), but AIS might not like it.)
    def select(self, index):
        self.log('action', 'Selecting "{}" in {}'.format(
            self.options[index].title, self.id))
        self.selected_index = index
        self._fire_event()

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        ev = selection_event(self, self.selected_index)
        self.dialog.app.send_events(ev)

    def changed_properties(self):
        index = '' if self.selected_index == -1 else self.selected_index
        cdata = ('<root><selection>'
            '<selectedIndexes>{}</selectedIndexes>'
            '</selection></root>').format(self.selected_index)
        return self._build_changed_properties(dataView=(True, True, cdata))

    def _ais_setDataView(self, id, body):
        data_view = body.find(id=id)
        container = data_view.find(id='radioBox_container', recursive=False)
        if not container:
            raise AISParseError("Expected radioBox_container")
        if container.name == 'span':
            self.selected_index = int(container['selectedindex'])
        else:
            self._parse_options(container.find(id='radioBox_items'))
    _ais_setDataView.wants_body = True
