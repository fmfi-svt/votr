from collections import namedtuple
from aisikl.components.control import Control
from aisikl.events import selection_event
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


Option = namedtuple('Option', ['title', 'id', 'tool_tip_text'])


class ComboBox(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.tool_tip_like_data = ct(bool, properties.get('ttld', False))
        self._parse_options(nn(element))

    def _parse_options(self, element: Tag) -> None:
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
    def selected_option(self) -> Option | None:
        if self.selected_index == -1: return None
        return self.options[self.selected_index]

    def select(self, index: int) -> None:
        self.log('action', 'Selecting "{}" in {}'.format(
            self.options[index].title, self.id))
        self.selected_index = index
        self._fire_event()

    def _fire_event(self) -> None:
        self.dialog.component_changes(self, False)
        ev = selection_event(self, self.selected_index)
        self.dialog.app.send_events(ev)

    @override
    def changed_properties(self) -> str:
        cdata = ('<root><selection>'
            '<selectedIndexes>{}</selectedIndexes>'
            '</selection></root>').format(self.selected_index)
        return self._build_changed_properties(dataView=(True, True, cdata))

    def _ais_setDataView(self, id: str, body: Tag) -> None:
        data_view = nn(body.find(id=id))
        combo_box_list = nn(data_view.find(id='comboBoxList', recursive=False))
        if combo_box_list.has_attr('selectedIndex_'):
            self.selected_index = int(ct(str, combo_box_list['selectedIndex_']))
        else:
            self._parse_options(combo_box_list)
        self.dialog.try_interactive(self, 'SelectionEvent')
    # pyrefly: ignore [missing-attribute]
    _ais_setDataView.wants_body = True
