from aisikl.components.component import is_true
from aisikl.components.control import Control
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


# Not a namedtuple, because 'checked' can change.
class Item:
    def __init__(self, title: str, id: str, sid: str, rid: str, tool_tip_text: str, checked: bool) -> None:
        self.title = title
        self.id = id
        self.sid = sid
        self.rid = rid
        self.tool_tip_text = tool_tip_text
        self.checked = checked

    @override
    def __repr__(self) -> str:
        return '<{} {}>'.format(self.__class__.__name__, repr(self.__dict__))


class CheckList(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_down_enabled = ct(bool, properties.get('upDownEnabled', False))
        self._parse_items(nn(element))

    def _parse_items(self, element: Tag) -> None:
        self.selected_index = -1
        self.items: list[Item] = []
        for index, tr in enumerate(element.find_all('tr')):
            td = nn(tr.td)
            self.items.append(Item(
                title=tr.get_text(),
                id=ct(str, td['id']), sid=ct(str, tr['sid']), rid=ct(str, tr['rid']),
                tool_tip_text=ct(str, td['title']),
                checked=nn(tr.input).has_attr('checked'),
            ))
            if 'selectedListRow' in (tr.get('class') or []):
                self.selected_index = index

    def up_down_row(self, command: str) -> None:
        raise Exception('up_down_row not yet implemented.')   # TODO

    def select_unselect_all(self) -> None:
        if not self.items: return
        new_value = not self.items[0].checked
        self.log('action', '{} all items in {}'.format(
            'Selecting' if new_value else 'Unselecting', self.id))
        for item in self.items:
            item.checked = new_value
        self._mark_changed()

    def select(self, index: int) -> None:
        self.log('action', 'Selecting item "{}" {}'.format(
            self.items[index].title, self.id))
        self.selected_index = index

    def toggle(self, index: int) -> None:
        self.items[index].checked = not self.items[index].checked
        self.log('action', '{} item "{}" in {}'.format(
            'Checking' if self.items[index].checked else 'Unchecking',
            self.items[index].title, self.id))
        self.selected_index = index
        self._mark_changed()

    def _ais_setUpDownEnabled(self, value: object) -> None:
        self.up_down_enabled = is_true(value)
    def _ais_setDataView(self, id: str, body: Tag) -> None:
        self._parse_items(nn(body.find(id=id)))
    _ais_setDataView.wants_body = True  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportFunctionMemberAccess]

    def _mark_changed(self) -> None:
        self.dialog.component_changes(self, False)

    @override
    def changed_properties(self) -> str:
        selection = ','.join(
            ('' if item.checked else '-') + item.rid for item in self.items)

        for index, item in enumerate(self.items):
            item.rid = str(index)

        cdata = ('<root><selection>'
            '<selectedIndexes>{}</selectedIndexes>'
            '</selection></root>').format(selection)
        return self._build_changed_properties(dataView=(True, True, cdata))
