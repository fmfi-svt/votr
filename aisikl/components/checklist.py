from aisikl.components.component import is_true
from aisikl.components.control import Control
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from aisikl.operations import Operations
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
        return f'<{self.__class__.__name__} {self.__dict__!r}>'


class CheckList(Control):
    """A list box widget where each item has a checkbox, and one item can be
    selected.
    """

    selected_index: int
    """Index of the selected item. -1 if none."""

    items: list[Item]

    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.up_down_enabled = ct(bool, properties.get('upDownEnabled', False))
        self._parse_items(nn(element))

    def _parse_items(self, element: Tag) -> None:
        self.selected_index = -1
        self.items = []
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

    async def up_down_row(self, command: str, *, return_ops: bool = False) -> Operations:
        """Moves the selected item up or down, if the list supports it. Not yet
        implemented.
        """
        raise Exception('up_down_row not yet implemented.')   # TODO

    async def select_unselect_all(self) -> None:
        """Checks or unchecks the checkbox of all items, depending on the first
        item's state (toggling it).
        """
        # TODO: This method is quite useless. webui.js has selectUnselectAll,
        # and calls it on Ctrl+A, but that doesn't mean Votr needs it too.
        if not self.items: return
        new_value = not self.items[0].checked
        log_verb = 'Selecting' if new_value else 'Unselecting'
        await self.log('action', f'{log_verb} all items in {self.id}')
        for item in self.items:
            item.checked = new_value
        self._mark_changed()

    async def select(self, index: int) -> None:
        """Selects the item at ``index``. Does not toggle its checkbox.

        Implemented for completeness to support the unlikely scenario that AIS
        cares about the selected item.
        """
        await self.log('action',
            f'Selecting item "{self.items[index].title}" {self.id}')
        self.selected_index = index

    async def toggle(self, index: int) -> None:
        """Toggles the checkbox of the item at ``index``, and selects it."""
        self.items[index].checked = not self.items[index].checked
        log_verb = 'Checking' if self.items[index].checked else 'Unchecking'
        await self.log('action', f'{log_verb} item "{self.items[index].title}" in {self.id}')
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
            f'<selectedIndexes>{selection}</selectedIndexes>'
            '</selection></root>')
        return self._build_changed_properties(dataView=(True, True, cdata))
