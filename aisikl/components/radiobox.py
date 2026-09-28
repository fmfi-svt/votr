from aisikl.components.control import Control
from aisikl.events import selection_event
from aisikl.exceptions import AISParseError
from aisikl.typeutils import ct, ct_none, nn
from typing import NamedTuple, TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from aisikl.operations import Operations
    from bs4.element import Tag


class Option(NamedTuple):
    title: str
    id: str | None


class RadioBox(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)

        items = nn(nn(element).find(id='radioBox_items'))
        self.always_selected = items.get('allwaysselected', 'false') == 'true'

        self._parse_options(items)

    def _parse_options(self, items: Tag) -> None:
        self.selected_index = -1
        self.options: list[Option] = []
        for index, td in enumerate(items.find_all('td')):
            if self.enabled and td['index'] != str(index):
                raise AISParseError(
                    f"RadioBox '{self.id}' item #{index} "
                    "has unexpected index attribute.")
            self.options.append(Option(
                title=nn(td.label).get_text(),
                id=ct_none(str, nn(td.input).get('sid')),
            ))
            if nn(td.input).has_attr('checked'):
                self.selected_index = index

    @property
    def selected_option(self) -> Option | None:
        if self.selected_index == -1: return None
        return self.options[self.selected_index]

    # If self.always_selected == False, select(-1) unselects the current item.
    # (Votr always allows select(-1), but AIS might not like it.)
    async def select(self, index: int, *, return_ops: bool = False) -> Operations:
        await self.log('action',
            f'Selecting "{self.options[index].title}" in {self.id}')
        self.selected_index = index
        return await self._fire_event(return_ops=return_ops)

    async def _fire_event(self, *, return_ops: bool) -> Operations:
        self.dialog.component_changes(self, False)
        ev = selection_event(self, self.selected_index)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    @override
    def changed_properties(self) -> str:
        index = '' if self.selected_index == -1 else self.selected_index
        cdata = ('<root><selection>'
            f'<selectedIndexes>{index}</selectedIndexes>'
            '</selection></root>')
        return self._build_changed_properties(dataView=(True, True, cdata))

    def _ais_setDataView(self, id: str, body: Tag) -> None:
        data_view = nn(body.find(id=id))
        container = data_view.find(id='radioBox_container', recursive=False)
        if not container:
            raise AISParseError("Expected radioBox_container")
        if container.name == 'span':
            self.selected_index = int(ct(str, container['selectedindex']))
        else:
            self._parse_options(nn(container.find(id='radioBox_items')))
    _ais_setDataView.wants_body = True  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportFunctionMemberAccess]
