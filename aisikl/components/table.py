import json
from bs4 import BeautifulSoup
from aisikl.components.action import Action
from aisikl.components.component import is_true
from aisikl.components.control import Control
from aisikl.components.combobox import Option
from aisikl.events import cell_edited_event, row_edited_event, action_event, selection_event, cursor_event, table_header_event
from aisikl.exceptions import AISParseError, AISBehaviorError
from aisikl.operations import Operations
from aisikl.typeutils import ct, ct_none, nn, really_int
from typing import NamedTuple, TYPE_CHECKING, cast, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from aisikl.events import Event
    from bs4.element import Tag
    from collections.abc import Iterable


class Column(NamedTuple):
    alias: str
    index: int  # pyright: ignore [reportIncompatibleMethodOverride] # TODO: stop using tuples?
    title: str | None
    header: str | None
    sortable: bool
    fixed: bool
    width: int
    visible: bool
    is_checked_selection_column: bool | None
    edited_by: str | None
    combo_box_mode: str | None
    model: str | None
    send_edit_cell: bool
    default_value: str | None


class Cell(NamedTuple):
    value: str | bool
    title: str | None
    edited_by: str | None
    combo_box_mode: str | None
    model: str | None
    send_edit_cell: bool
    disabled: bool


class Row:
    def __init__(self, id: int, rid: str, cells: list[Cell], table: Table) -> None:
        self.id = id
        self.rid = rid
        self.cells = cells
        self.table = table

    def cell(self, column_name: str) -> Cell:
        '''Returns the cell in this row and ``column_name``.'''
        return self.cells[self.table.column_map[column_name].index]

    def __getitem__(self, column_name: str) -> str:
        r'''Returns the string cell value in this row and ``column_name``.
        Raises if the cell contains a checkbox instead of a string (checkboxes
        can be read with ``row.cell(name).value``).
        '''
        return ct(str, self.cell(column_name).value)

    @override
    def __repr__(self) -> str:
        return f'Row({self.id!r}, {self.rid!r}, {self.cells!r})'


def load_script_plain(data_view: Tag, id: str) -> str | None:
    script_element = data_view.find(id=id)
    if not script_element: return None
    if script_element.name != 'script':
        raise AISParseError(f'Expected {id} to be script instead of {script_element.name}')
    return script_element.get_text()[4:-3]   # always "<!--" and "-->"


def load_script(data_view: Tag, id: str) -> Tag | None:
    text = load_script_plain(data_view, id)
    if text is None: return None
    return BeautifulSoup(text, 'lxml')   # note: will be wrapped in <html> and <body>


class Table(Control):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)

        # In the original JavaScript, these properties have default values, but
        # it seems the server always sets them. If it stops sending them, maybe
        # it's better to fail loudly. The original default value of each
        # property is written in the comment.
        self.sortable = ct(bool, properties['sortable'])  # True
        self.always_selected = ct(bool, properties['allwaysSelected'])  # True
        self.fixed_columns = ct(int, properties.get('fixedColumns', 0))
        self.up_down_enabled = ct(bool, properties['upDownEnabled'])  # False
        self.user_add_remove_rows_enabled = ct(bool, properties['userAddRemoveRowsEnabled'])  # False
        self.supported_events = ct(str, properties.get('se') or '')
        self.multiple_selection = ct(bool, properties['multipleSelection'])  # False
        self.cell_selection_mode = ct(bool, properties['cellSelectionMode'])  # False
        self.scroll_bottom_enabled = ct(bool, properties['scrollBottomEnabled'])  # False
        self.select_all_enabled = ct(bool, properties['selectAllEnabled'])  # False
        self.row_numbers_visible = ct(bool, properties['rowNumbersVisible'])  # False
        self.row_numbers_visible_changed = False
        self.status_visible = ct(bool, properties['statusVisible'])  # False
        self.status_visible_changed = False
        self.visible_status_buttons = ct(int, properties['visibleStatusButtons'])  # 0

        self.is_end_of_data = False
        self.truncated = False
        self.row_count = 0
        self.declared_row_count = 0
        self.no_data_loaded = False

        self.cursor_row_index: int | None = None
        self.selected_row_indexes = []
        self.selected_column_alias: str | None = None
        self.inverted_selection = False
        self.selection_changed = False
        self.active_index_changed = False

        self.buffer_size = ct(int, properties.get('bufferSize', 50))

        self.headers_changed = False
        self.up_downed_rows = False
        self.deleted_rows = False
        self.edited_cells = False
        self.scrolled_vertically = False

        self.action_name = ct_none(str, properties.get('an'))

        self.columns: list[Column] = []
        self.column_map: dict[str, Column] = {}
        self.num_visible_buffers = 1
        self.loaded_buffers: set[int] = set()
        self.loaded_rows: list[Row] = []  # That's a lie. It's actually list[Row | None].
        self.combobox_options: dict[str, list[Option]] = {}
        self.changed_cells: set[tuple[str, int]] = set()
        self.last_changed_row_index: int | None = None

    @override
    async def async_init(self, element: Tag | None) -> None:
        await self._init_from_data_view(nn(element).find(id=self.id + '_dataView'))

    async def _init_from_data_view(self, data_view: Tag | None) -> None:
        if not data_view: return

        self._update_data_position_properties(data_view)
        self._update_selection_model_properties(data_view)
        self._update_data_tab_bodies_properties(data_view)

        properties = json.loads(nn(load_script_plain(data_view, 'json')))

        self.columns = []

        index = 0
        for fixed in [True, False]:
            suffix = 'Fixed' if fixed else ''
            header_table = load_script(data_view, 'columnModel' + suffix)
            colgroup = load_script(data_view, 'dataTabColGroup' + suffix)
            if not header_table: continue
            tds = { e['id']: e for e in header_table.find_all(id=True) }
            for col in nn(colgroup).find_all('col'):
                alias = ct(str, col['id'])
                col_properties: dict[str, object] = properties['columns'][alias]
                td = tds['hdr-' + alias]
                width = int(ct(str, col.get('width', '0')).partition('px')[0])
                self.columns.append(Column(
                    alias=alias,
                    index=index,
                    title=ct_none(str, td.get('title')),
                    header=ct_none(str, td.get('header')),
                    sortable=ct(bool, col_properties.get('s', False)),
                    fixed=fixed,
                    width=width,
                    visible=not col_properties.get('h', False),
                    is_checked_selection_column=ct_none(bool, col_properties.get('ch')),
                    edited_by=ct_none(str, col.get('editedby')),
                    combo_box_mode=ct_none(str, col.get('cbmode')),
                    model=ct_none(str, col.get('model')),
                    send_edit_cell=col.get('sendeditcell', 'false') == 'true',
                    default_value=ct_none(str, col.get('defaultvalue')),
                ))
                index += 1

        self.column_map = { col.alias: col for col in self.columns }

        await self.log('table', f'Found {len(self.columns)} columns in {self.id}', self.columns)

        await self._load_rows(nn(load_script(data_view, 'dataTabBodies')),
                              load_script(data_view, 'dataTabBodiesFixed'))

        self._load_edit_models(load_script(data_view, 'dataTabEditModels'))

        # onload calls initTableModel which calls initPropertiesAndModels which calls this:
        #self._show_control_buttons()
        #self._table_model_update(-1, -1, False)
        # TODO remove me but document it

    def _update_data_position_properties(self, data_view: Tag | None) -> None:
        if not data_view: return
        element = data_view.find(id='dataPositionSpan')
        if not element: return
        self.is_end_of_data = element.get('isend', 'false') == 'true'
        self.truncated = element.get('truncated', 'false') == 'true'
        self.fixed_columns = int(ct(str, element.get('fixedcolumns', '0')))

    def _update_data_tab_bodies_properties(self, data_view: Tag | None) -> None:
        if not data_view: return
        element = data_view.find(id='dataTabBodies')
        if not element: return
        self._ais_setBufferSize(element.get('buffersize'))

    def _update_selection_model_properties(self, data_view: Tag | None) -> None:
        if not data_view: return
        element = data_view.find(id='selectionModel')
        if not element: return

        # TODO: loaded_rows chcem aby isiel po ID-ckach, to jest loaded_rows[0] je row ktory ma id=row_0 a nie nutne najvyssi
        # ledaze by nie??? vyzera ze AIS v tom ma tiez taky bordel ako my
        # TODO: velky audit celeho webui kedy sa pouziva row_ resp substring(4) a kedy nie

        was_multiple_selection = len(self.selected_row_indexes) > 1

        selection = [int(id) for id in ct(str, element.get('selection', '')).split(',') if id]
        if self.cell_selection_mode:
            selection = selection[0:1] if selection else [0]
        self.selected_row_indexes = selection

        if self.cell_selection_mode:
            self.selected_column_alias = ct_none(str, element.get(
                'cellselectionalias', self.selected_column_alias))
        else:
            self.selected_column_alias = None

        self.row_count = int(ct(str, element['rowcount']))
        self.declared_row_count = int(ct(str, element['declaredrowcount']))
        self.no_data_loaded = element.get('nodataloaded', 'false') == 'true'

        if selection:
            if (activeindex := element.get('activeindex')) is not None:
                self.cursor_row_index = int(ct(str, activeindex))
            else:
                self.cursor_row_index = selection[0]
        elif self.row_count or self.declared_row_count:
            self.cursor_row_index = 0
        else:
            self.cursor_row_index = None

        self.inverted_selection = (not self.cell_selection_mode and
            element.get('invertedselection', 'false') == 'true')

        is_multiple_selection = len(self.selected_row_indexes) > 1
        if was_multiple_selection != is_multiple_selection:
            self.dialog.try_interactive(self, "switchMultiple")

        self.selection_changed = True

    def _ais_setSortable(self, value: object) -> None:
        self.sortable = is_true(value)
        # TODO: this.tableService.updateStatusControlSortButton
    def _ais_setAllwaysSelected(self, value: object) -> None:
        self.always_selected = is_true(value)
    def _ais_setFixedColumns(self, value: object) -> None:
        self.fixed_columns = really_int(value)
    def _ais_setMinNoFixedColumnsWidth(self, value: object) -> None:
        pass   # getMinNoFixedColumnsWidth is unused in Votr
    def _ais_setUpDownEnabled(self, value: object) -> None:
        self.up_down_enabled = is_true(value)
    def _ais_setUserAddRemoveRowsEnabled(self, value: object) -> None:
        self.user_add_remove_rows_enabled = is_true(value)
    def _ais_setSupportedEvents(self, value: object) -> None:
        self.supported_events = ct(str, value)
    def _ais_setMultipleSelection(self, value: object) -> None:
        self.multiple_selection = is_true(value)
    def _ais_setCellSelectionMode(self, value: object) -> None:
        self.cell_selection_mode = is_true(value)
    def _ais_setScrollBottomEnabled(self, value: object) -> None:
        self.scroll_bottom_enabled = is_true(value)
    def _ais_setSelectAllEnabled(self, value: object) -> None:
        self.select_all_enabled = is_true(value)
    def _ais_setRowNumbersVisible(self, value: object) -> None:
        self.row_numbers_visible = is_true(value)
    def _ais_setStatusVisible(self, value: object) -> None:
        self.status_visible = is_true(value)
    def _ais_setVisibleStatusButtons(self, value: object) -> None:
        self.visible_status_buttons = really_int(value)
    def _ais_setBufferSize(self, value: object) -> None:
        self.buffer_size = 50 if value is None else really_int(value)

    async def switch_row_numbers_visible(self) -> None:
        await self.log('action', f'Switching row numbers visibility in {self.id}')
        self.row_numbers_visible = not self.row_numbers_visible
        self.row_numbers_visible_changed = True
        self.dialog.component_changes(self, True)

    async def switch_status_visible(self) -> None:
        await self.log('action', f'Switching status bar visibility in {self.id}')
        self.status_visible = not self.status_visible
        self.status_visible_changed = True
        self.dialog.component_changes(self, True)

    async def on_column_move(self, column_alias: str, after_column_alias: str, *, return_ops: bool = False) -> Operations: # TODO inline into actual column move fn
        await self.log('action', f'Moving {column_alias} to be after {after_column_alias} in {self.id}')
        ev = table_header_event(
            self, column_alias, after_column_alias, None, 'MOVE_COLUMN')
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def _on_edit_row(self, index: int, *, return_ops: bool = False) -> Operations:
        if not self.edited_cells: return Operations()
        self.dialog.component_changes(self, False)
        if 'EDITED_ROW|' in self.supported_events:
            self.used_listeners_mask |= 64
            ev = row_edited_event(self, 'EDITED_ROW', index)
            return await self.dialog.app.send_events(ev, return_ops=return_ops)
        else:
            return Operations()

    async def sort(self, column_alias: str, modifiers: str | None, *, return_ops: bool = False) -> Operations:
        # TODO: find out if this should be a public function
        ev = table_header_event(
            self, column_alias, None, modifiers, 'HEADER_CLICK')
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def _on_data_tab_dbl_click(self, *, return_ops: bool = False) -> Operations:
        # TODO: rename or inline this appropriately
        if self.action_name:
            action = self.dialog.components[self.action_name]
            if action:
                return await ct(Action, action).execute(self.id, return_ops=return_ops)
        if 'EMPTY|' in self.supported_events:
            self.used_listeners_mask |= 64
            ev = action_event(self, None, self.id)
            return await self.dialog.app.send_events(ev, return_ops=return_ops)
        return Operations()

    async def _fire_action_command(self, command: str, *, return_ops: bool) -> Operations:
        if command + '|' in self.supported_events:
            self.used_listeners_mask |= 64
            ev = action_event(self, command, self.id)
            return await self.dialog.app.send_events(ev, return_ops=return_ops)
        else:
            return Operations()

    async def delete_row(self, *, return_ops: bool = False) -> Operations:
        self.dialog.component_changes(self, False)
        return await self._fire_action_command('DELETE_ROW', return_ops=return_ops)

    async def insert_row(self, *, return_ops: bool = False) -> Operations:
        self.dialog.component_changes(self, False)
        return await self._fire_action_command('INSERT_ROW', return_ops=return_ops)

    async def control_button_row_count(self, *, return_ops: bool = False) -> Operations:
        self.dialog.component_changes(self, True)
        return await self._fire_action_command('ROW_COUNT', return_ops=return_ops)

    async def control_button_columns(self, *, return_ops: bool = False) -> Operations:
        self.dialog.component_changes(self, True)
        return await self._fire_action_command('SET_COLUMNS', return_ops=return_ops)

    async def control_button_sort(self, *, return_ops: bool = False) -> Operations:
        self.dialog.component_changes(self, True)
        return await self._fire_action_command('SET_SORTING', return_ops=return_ops)

    async def control_button_debug_info(self, *, return_ops: bool = False) -> Operations:
        self.dialog.component_changes(self, True)
        return await self._fire_action_command('DEBUG_INFO', return_ops=return_ops)

    async def up_down_row(self, command: str, *, return_ops: bool = False) -> Operations:
        if not self.up_down_enabled: return Operations()
        if self._table_model_up_down(command):   # TODO: not implemented yet # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]
            self.up_downed_rows = True
            self.dialog.component_changes(self, False)
        return Operations()

    async def _on_edit_cell(self, send: bool, alias: str, row_index: int, *, return_ops: bool = False) -> Operations:
        self.edited_cells = True
        self.dialog.component_changes(self, False)
        if not send:
            return Operations()
        if 'EDITED_CELL|' not in self.supported_events:
            return Operations()
        self.used_listeners_mask |= 64
        ev = cell_edited_event(self, 'EDITED_CELL', alias, row_index)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def button_num_code_click(self, alias: str, row_index: int, value: str | bool, *, return_ops: bool = False) -> Operations:
        await self.edit_cell(alias, row_index, value, _skip_event=True)

        self.edited_cells = True
        self.dialog.component_changes(self, False)
        if 'BUTTON_NUM_CODE|' not in self.supported_events: return Operations()
        self.used_listeners_mask |= 64
        ev = cell_edited_event(self, 'BUTTON_NUM_CODE', alias, row_index)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    @override
    def changed_properties(self) -> str:
        cdata = ['<root>']

        if self.selection_changed or self.active_index_changed:
            cdata.append("<selection{}>".format(" invertedSelection='true'" if self.inverted_selection else ""))
            cdata.append(f"<activeIndex>{-1 if self.cursor_row_index is None else self.cursor_row_index}</activeIndex>")
            cdata.append("<selectedIndexes>{}</selectedIndexes>".format(','.join(map(str, self.selected_row_indexes))))
            cdata.append("</selection>")
            if self.selected_column_alias:
                cdata.append(f"<selectedColumnAlias>{self.selected_column_alias}</selectedColumnAlias>")
            self.selection_changed = False
            # TODO: AIS doesn't do it, but we should probably unset active_index_changed too

        if self.headers_changed:
            json_columns = json.dumps(
                [{ "id": column.alias, "width": column.width }
                 for column in self.columns])
            cdata.append(f"<JSONcolumns>{json_columns}</JSONcolumns>")
            self.headers_changed = False

        if self.scrolled_vertically:
            cdata.append("<visibleBuffers>{}</visibleBuffers>".format(
                ','.join(map(str, range(self.num_visible_buffers)))))
            cdata.append("<loadedBuffers>{}</loadedBuffers>".format(
                ','.join(map(str, sorted(self.loaded_buffers)))))
            self.scrolled_vertically = False

        if self.edited_cells:
            cdata.append("<editedCells>")
            for alias, row_index in sorted(self.changed_cells):
                column = self.column_map[alias]
                cell = self.loaded_rows[row_index].cells[column.index]
                edited_by = cell.edited_by or column.edited_by
                value = cell.value
                if edited_by == 'checkBox':
                    type = 'boolean'
                    value = 'true' if value else 'false'
                elif edited_by == 'dateControl':
                    type = 'date'
                elif edited_by == 'numberControl':
                    type = 'number'
                else:
                    type = 'string'
                cdata.append(f"<cell row='{row_index}' alias='{alias}' type='{type}'>{value}</cell>")
            cdata.append("</editedCells>")
            self.changed_cells.clear()
            self.last_changed_row_index = None
            self.edited_cells = False

        if self.deleted_rows or self.up_downed_rows:
            cdata.append(f"<upDownedRows>{self._get_rows_ids()}</upDownedRows>")   # TODO: not implemented yet # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]
            self._table_model_reset_rows_ids()   # TODO: not implemented yet # pyrefly: ignore [missing-attribute] # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType]
            self.deleted_rows = False
            self.up_downed_rows = False

        cdata.append("</root>")

        properties: dict[str, tuple[bool, bool, str | bool]] = {}
        properties['dataView'] = (True, True, ''.join(cdata))
        properties['editMode'] = (False, False, False)

        if self.status_visible_changed:
            properties['statusVisible'] = (False, False, self.status_visible)
            self.status_visible_changed = False

        if self.row_numbers_visible_changed:
            properties['rowNumbersVisible'] = (False, False, self.row_numbers_visible)
            self.row_numbers_visible_changed = False

        return self._build_changed_properties(**properties)

    async def _ais_setDataView(self, id: str, body: Tag) -> None:
        data_view = nn(body.find(id=id))
        if not data_view.contents: return
        if data_view.find(id='columnModel'):
            await self._init_from_data_view(data_view)
        else:
            await self._update_data(data_view)
    _ais_setDataView.wants_body = True  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportFunctionMemberAccess]

    async def _update_data(self, data_view: Tag) -> None:
        self._update_selection_model_properties(data_view)

        data_tab_bodies = data_view.find(id='dataTabBodies')
        data_tab_bodies_fixed = data_view.find(id='dataTabBodiesFixed')
        if not data_tab_bodies: return

        self._update_data_tab_bodies_properties(data_view)
        self._update_data_position_properties(data_view)

        data_send_type = data_tab_bodies.get('datasendtype', 'update')
        if data_send_type == 'info':
            await self.log('table', f'Updating info in {self.id}')
            return

        if data_tab_bodies.find(id='dataTabTmp'):
            if not data_tab_bodies.tbody:
                # This might be a behavior difference - WebUI actually does
                # `this.dataSendType == "update";`. We hope they meant `=`.
                data_send_type = 'update'
            await self._load_rows(data_tab_bodies, data_tab_bodies_fixed,
                            replace=(data_send_type == 'update'))

        self._load_edit_models(data_view.find(id='dataTabEditModels'))

    async def _load_rows(self, data_tab_bodies: Tag, data_tab_bodies_fixed: Tag | None, replace: bool=True) -> None:
        really_replaced = replace and self.loaded_rows
        if replace:
            self.loaded_buffers = set()
            self.loaded_rows = []
            self.num_visible_buffers = 0

        for tbody in data_tab_bodies.find_all('tbody'):
            id = int(ct(str, tbody['id'])[len('dataTabBody'):])
            self.loaded_buffers.add(id)
            if self.num_visible_buffers < id + 1:
                self.num_visible_buffers = id + 1

        fixed_trs: dict[str, Tag] = {}
        if data_tab_bodies_fixed:
            for tr in data_tab_bodies_fixed.find_all('tr'):
                fixed_trs[ct(str, tr['id'])] = tr

        new_rows: dict[int, list[str | bool]] = {}
        for tr in data_tab_bodies.find_all('tr'):
            # Skip trs added for accessibility reasons
            if tr['id'] == 'aria-columns-row':
                continue

            id = int(ct(str, tr['id'])[len('row_'):])
            rid = ct(str, tr['rid'])
            tds = tr.find_all('td')
            if data_tab_bodies_fixed:
                tds = fixed_trs[ct(str, tr['id'])].find_all('td') + tds
            cells = [self._load_cell(td) for td in tds]
            new_rows[id] = [cell.value for cell in cells]
            row = Row(id, rid, cells, self)

            while len(self.loaded_rows) <= row.id:
                self.loaded_rows.append(cast(Row, cast(object, None)))  # For ease of use, lie to the type checker.
            self.loaded_rows[row.id] = row

        await self.log('table', 'Loaded {} rows in {}{}'.format(
            len(new_rows), self.id,
            ' (replacing old content)' if really_replaced else ''),
            new_rows)

    def _load_cell(self, td: Tag) -> Cell:
        value = td.get_text()
        if value == '\xa0': value = ''

        if td.get('datatype') == 'boolean':
            value = bool(td.find(class_='booleanCellChecked'))

        if td.get('datatype') == 'image':
            value = ct(str, nn(td.img)['src'])

        checkbox = td.find('input', type='checkbox')
        if checkbox:
            return Cell(
                value=bool(checkbox.get('checked')),
                title=None,
                edited_by='checkBox',
                combo_box_mode=None,
                model=None,
                send_edit_cell=checkbox.get('sendeditcell', 'false') == 'true',
                disabled=checkbox.get('disabled', 'false') == 'true',
            )

        return Cell(
            value=value,
            title=ct_none(str, td.get('title')),
            edited_by=ct_none(str, td.get('editedby')),
            combo_box_mode=ct_none(str, td.get('cbmode')),
            model=ct_none(str, td.get('model')),
            send_edit_cell=td.get('sendeditcell', 'false') == 'true',
            disabled=td.get('disabled', 'false') == 'true',
        )

    def _load_edit_models(self, data_tab_edit_models: Tag | None) -> None:
        if not data_tab_edit_models: return

        self.combobox_options = {}

        for select in data_tab_edit_models.find_all('select'):
            options: list[Option] = []
            self.combobox_options[ct(str, select['id'])] = options
            for option in select.find_all('option'):
                options.append(Option(
                    title=option.get_text(),
                    id=ct(str, option['sid']),
                    tool_tip_text=ct(str, option['title']),
                ))

    async def scroll_down(self, buffers: int=1, *, return_ops: bool = False) -> Operations:
        if self.is_end_of_data: return Operations()
        await self.log('action', f'Scrolling down in {self.id}')
        self.num_visible_buffers += buffers
        self.scrolled_vertically = True
        self.dialog.component_changes(self, True)
        ev = cursor_event(self, 'pagedown', 'PAGEDOWN')
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    async def all_rows(self) -> list[Row]:
        if self.declared_row_count > 0:
            await self.scroll_down(self.declared_row_count // self.buffer_size + 1)

        while not self.is_end_of_data:
            await self.scroll_down(10)
        if self.truncated:
            raise AISBehaviorError("AIS did not return all table rows")
        return self.loaded_rows

    async def select(self, indexes: int | Iterable[int], cursor: int | None=None, inverted: bool=False, column_alias: str | None=None, *, _skip_event: bool=False, return_ops: bool = False) -> Operations:
        if isinstance(indexes, int):
            indexes = [indexes]
        else:
            indexes = sorted(set(indexes))

        if cursor is None:
            # Votr combines row-by-row selection into a single select() call to
            # be simpler to use, so we try to guess the final cursor position.
            # When it matters, it's better to specify it explicitly.
            if indexes:
                cursor = indexes[-1]
            elif self.cursor_row_index is not None and not inverted:
                cursor = self.cursor_row_index
            else:
                cursor = 0

        if self.cell_selection_mode:
            if column_alias is None:
                # If a user turns on JAWS support mode in AIS user preferences,
                # all tables will be in cell selection mode.
                column_alias = self.selected_column_alias
            if len(indexes) != 1:
                raise AISBehaviorError('can\'t select multiple rows in cell selection mode')
        else:
            if column_alias is not None:
                raise AISBehaviorError('column selection not supported for this table')

        if inverted and not (self.multiple_selection and self.select_all_enabled):
            raise AISBehaviorError('inverted selection not supported for this table')
        if len(indexes) > 1 and not self.multiple_selection:
            raise AISBehaviorError('multiple selection not supported for this table')
        if self.always_selected and ((not inverted and len(indexes) == 0) or
                (inverted and len(indexes) == len(self.loaded_rows))):
            raise AISBehaviorError('empty selection not supported for this table')

        await self.log('action', 'Selecting {}{}{} {}{} in {}'.format(
            f'column {column_alias} of ' if column_alias else '',
            'inverted ' if inverted else '',
            'rows' if len(indexes) > 1 else 'row',
            ', '.join(map(str, indexes)),
            f' with cursor at {cursor}' if indexes != [cursor] else '',
            self.id))

        was_multiple_selection = len(self.selected_row_indexes) > 1
        is_multiple_selection = len(indexes) > 1
        active_index_changed = self.cursor_row_index != cursor
        selection_changed = (
            self.selected_row_indexes != indexes or
            self.inverted_selection != inverted or
            self.selected_column_alias != column_alias)

        self.selected_row_indexes = indexes
        self.cursor_row_index = cursor
        self.inverted_selection = inverted
        self.selected_column_alias = column_alias

        operations = Operations()

        if was_multiple_selection != is_multiple_selection:
            self.dialog.try_interactive(self, "switchMultiple")

        if active_index_changed:
            self.active_index_changed = True
            self.dialog.component_changes(self, True)
            operations.extend(await self._fire_action_command('ACTIVE_ROW_CHANGE', return_ops=return_ops))

        if selection_changed:
            self.selection_changed = True
            self.dialog.component_changes(self, True)

        if selection_changed and not _skip_event:
            evs: list[Event] = []
            if self.edited_cells:
                if self.last_changed_row_index is not None:
                    self.dialog.component_changes(self, False)
                    if 'EDITED_ROW|' in self.supported_events:
                        self.used_listeners_mask |= 64
                        evs.append(row_edited_event(self, 'EDITED_ROW', self.last_changed_row_index))
            # This only emits a selection event for the final selected row (in
            # case of multiple selection). That is a bit unfortunate, but WebUI
            # already had this "problem" when Shift+selecting, so it should be
            # OK for Votr. You could always call select() many times if needed.
            evs.append(selection_event(self, cursor, cursor in indexes))
            operations.extend(await self.dialog.app.send_events(*evs, return_ops=return_ops))

        return operations

    async def edit_cell(self, alias: str, row_index: int, value: str | bool, *, _skip_event: bool=False, return_ops: bool = False) -> Operations:
        column = self.column_map[alias]
        row = self.loaded_rows[row_index]
        cell = row.cells[column.index]
        is_checkbox = cell.edited_by == 'checkBox'

        if not is_checkbox:
            send_edit_cell = cell.send_edit_cell or column.send_edit_cell
        else:
            # checkboxes ignore the column's send_edit_cell
            send_edit_cell = cell.send_edit_cell
            value = bool(value)

        operations = await self.select(row_index,
            column_alias=(alias if self.cell_selection_mode else None),
            _skip_event=(is_checkbox and send_edit_cell),
            return_ops=return_ops)

        await self.log('action', f'Setting cell {alias} of row {row_index} in {self.id} to {value!r}')

        cell = row.cells[column.index] = cell._replace(value=value)

        self.changed_cells.add((alias, row_index))
        self.last_changed_row_index = row_index

        if not _skip_event:
            operations.extend(await self._on_edit_cell(send_edit_cell, alias, row_index))

        return operations
