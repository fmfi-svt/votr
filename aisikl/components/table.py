
from bs4 import BeautifulSoup
from collections import namedtuple
from .control import Control
from .combobox import Option
from aisikl.events import (cell_edited_event, row_edited_event, action_event,
                           selection_event, cursor_event, table_header_event)
from aisikl.exceptions import AISParseError, AISBehaviorError


Column = namedtuple('Column', [
    'alias', 'index', 'title', 'header', 'sortable', 'fixed', 'width',
    'visible', 'edited_by', 'combo_box_mode', 'model', 'send_edit_cell',
    'default_value'])


Cell = namedtuple('Cell', [
    'value', 'title', 'edited_by', 'combo_box_mode', 'model', 'send_edit_cell',
    'disabled'])


class Row(object):
    def __init__(self, id, rid, cells, table):
        self.id = id
        self.rid = rid
        self.cells = cells
        self.table = table

    def __getitem__(self, name):
        if isinstance(name, int):
            return self.cells[name].value
        return self.cells[self.table.column_map[name].index].value

    def __len__(self):
        return len(self.cells)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.cells)[1:-1])


def load_script(data_view, id):
    script_element = data_view.find(id=id)
    if not script_element: return None
    if script_element.name != 'script':
        raise AISParseError('Expected {} to be script instead of {}'.format(
            id, script_element.name))
    text = script_element.get_text()[4:-3]   # always "<!--" and "-->"
    return BeautifulSoup(text, 'lxml')   # note: will be wrapped in <html> and <body>


class Table(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)

        self.sortable = element.get('sortable', 'true') == 'true'
        self.always_selected = element.get('allwaysselected', 'true') == 'true'
        self.fixed_columns = int(element.get('fixedcolumns', '0'))
        self.up_down_enabled = element.get('updownenabled', 'false') == 'true'
        self.read_only = element.get('readonly', 'true') == 'true'
        self.user_add_remove_rows_enabled = element.get('useraddremoverowsenabled', 'false') == 'true'
        self.supported_events = element.get('supportedevents', '')
        self.multiple_selection = element.get('multipleselection', 'false') == 'true'
        self.cell_selection_mode = element.get('cellselectionmode', 'false') == 'true'
        self.scroll_bottom_enabled = element.get('scrollbottomenabled', 'false') == 'true'
        self.select_all_enabled = element.get('selectallenabled', 'false') == 'true'
        self.row_numbers_visible = element.get('rownumbersvisible', 'false') == 'true'
        self.row_numbers_visible_changed = False
        self.status_visible = element.get('statusvisible', 'false') == 'true'
        self.status_visible_changed = False
        self.visible_status_buttons = int(element.get('visiblestatusbuttons', '0'))

        self.is_end_of_data = False
        self.truncated = False
        self.row_count = 0
        self.declared_row_count = 0
        self.no_data_loaded = False

        self.cursor_row_index = None
        self.selected_row_indexes = []
        self.selected_column_alias = None
        self.inverted_selection = False
        self.selection_changed = False
        self.active_index_changed = False

        self.buffer_size = int(element.get('buffersize', '50'))

        self.headers_changed = False
        self.up_downed_rows = False
        self.deleted_rows = False
        self.edited_cells = False
        self.scrolled_vertically = False

        self.action_name = element.get('actionname')

        self.columns = []
        self.column_map = {}
        self.num_visible_buffers = 1
        self.loaded_buffers = set()
        self.loaded_rows = []
        self.combobox_options = {}
        self.changed_cells = set()
        self.last_changed_row_index = None

        self._init_from_data_view(element.find(id=self.id + '_dataView'))

    def _init_from_data_view(self, data_view):
        if not data_view: return

        self._update_data_position_properties(data_view)
        self._update_selection_model_properties(data_view)
        self._update_data_tab_bodies_properties(data_view)

        self.columns = []

        index = 0
        for fixed in [True, False]:
            suffix = 'Fixed' if fixed else ''
            header_table = load_script(data_view, 'columnModel' + suffix)
            colgroup = load_script(data_view, 'dataTabColGroup' + suffix)
            if not header_table: continue
            for col in colgroup.find_all('col'):
                td = header_table.find(shortname=col['shortname'])
                sortable = col.get('sortable', 'true') == 'true'
                width = int(col.get('width', '0').partition('px')[0])
                visible = 'hidden' not in col.get('style', '')
                self.columns.append(Column(
                    alias=col['shortname'], index=index, title=td.get('title'),
                    header=td.get('header'), sortable=sortable, fixed=fixed,
                    width=width, visible=visible, edited_by=col.get('editedby'),
                    combo_box_mode=col.get('cbmode'), model=col.get('model'),
                    send_edit_cell=col.get('sendeditcell', 'false') == 'true',
                    default_value=col.get('defaultvalue')))
                index += 1

        self.column_map = { col.alias: col for col in self.columns }

        self.log('table', 'Found {} columns in {}'.format(len(self.columns), self.id), self.columns)

        self._load_rows(load_script(data_view, 'dataTabBodies'),
                        load_script(data_view, 'dataTabBodiesFixed'))

        self._load_edit_models(load_script(data_view, 'dataTabEditModels'))

        # onload calls initTableModel which calls initPropertiesAndModels which calls this:
        #self._show_control_buttons()
        #self._table_model_update(-1, -1, False)
        # TODO remove me but document it

    def _update_data_position_properties(self, data_view):
        if not data_view: return
        element = data_view.find(id='dataPositionSpan')
        if not element: return
        self.is_end_of_data = element.get('isend', 'false') == 'true'
        self.truncated = element.get('truncated', 'false') == 'true'
        self.fixed_columns = int(element.get('fixedcolumns', '0'))

    def _update_data_tab_bodies_properties(self, data_view):
        if not data_view: return
        element = data_view.find(id='dataTabBodies')
        if not element: return
        self.buffer_size = int(element.get('buffersize'))   # I hope this won't break anything

    def _update_selection_model_properties(self, data_view):
        if not data_view: return
        element = data_view.find(id='selectionModel')
        if not element: return

        # TODO: loaded_rows chcem aby isiel po ID-ckach, to jest loaded_rows[0] je row ktory ma id=row_0 a nie nutne najvyssi
        # ledaze by nie??? vyzera ze AIS v tom ma tiez taky bordel ako my
        # TODO: velky audit celeho webui kedy sa pouziva row_ resp substring(4) a kedy nie

        was_multiple_selection = len(self.selected_row_indexes) > 1

        selection = [int(id) for id in element.get('selection', '').split(',') if id]
        if self.cell_selection_mode:
            selection = selection[0:1] if selection else [0]
        self.selected_row_indexes = selection

        if self.cell_selection_mode:
            self.selected_column_alias = element.get(
                'cellselectionalias', self.selected_column_alias)
        else:
            self.selected_column_alias = None

        self.row_count = int(element.get('rowcount'))
        self.declared_row_count = int(element.get('declaredrowcount'))
        self.no_data_loaded = element.get('nodataloaded', 'false') == 'true'

        if selection:
            self.cursor_row_index = int(element.get(
                'activeindex', selection[0]))
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

    def _ais_setSortable(self, value):
        self.sortable = (value == 'true')
        # TODO: this.tableService.updateStatusControlSortButton
    def _ais_setAllwaysSelected(self, value):
        self.always_selected = (value == 'true')
    def _ais_setFixedColumns(self, value):
        self.fixed_columns = int(value)
    def _ais_setMinNoFixedColumnsWidth(self, value):
        pass   # getMinNoFixedColumnsWidth is unused in Votr
    def _ais_setUpDownEnabled(self, value):
        self.up_down_enabled = (value == 'true')
    def _ais_setUserAddRemoveRowsEnabled(self, value):
        self.user_add_remove_rows_enabled = (value == 'true')
    def _ais_setSupportedEvents(self, value):
        self.supported_events = value
    def _ais_setMultipleSelection(self, value):
        self.multiple_selection = (value == 'true')
    def _ais_setCellSelectionMode(self, value):
        self.cell_selection_mode = (value == 'true')
    def _ais_setScrollBottomEnabled(self, value):
        self.scroll_bottom_enabled = (value == 'true')
    def _ais_setSelectAllEnabled(self, value):
        self.select_all_enabled = (value == 'true')
    def _ais_setRowNumbersVisible(self, value):
        self.row_numbers_visible = (value == 'true')
    def _ais_setStatusVisible(self, value):
        self.status_visible = (value == 'true')
    def _ais_setVisibleStatusButtons(self, value):
        self.visible_status_buttons = int(value)
    def _ais_setBufferSize(self, value):
        self.buffer_size = int(value)

    def switch_row_numbers_visible(self):
        self.log('action', 'Switching row numbers visibility in {}'.format(self.id))
        self.row_numbers_visible = not self.row_numbers_visible
        self.row_numbers_visible_changed = True
        self.dialog.component_changes(self, True)

    def switch_status_visible(self):
        self.log('action', 'Switching status bar visibility in {}'.format(self.id))
        self.status_visible = not self.status_visible
        self.status_visible_changed = True
        self.dialog.component_changes(self, True)

    def on_column_move(self, column_alias, after_column_alias): # TODO inline into actual column move fn
        self.log('action', 'Moving {} to be after {} in {}'.format(
            column_alias, after_column_alias, self.id))
        ev = table_header_event(
            self, column_alias, after_column_alias, None, 'MOVE_COLUMN')
        self.dialog.app.send_events(ev)

    def _on_edit_row(self, index):
        if not self.edited_cells: return
        self.dialog.component_changes(self, False)
        if 'EDITED_ROW|' in self.supported_events:
            self.used_listeners_mask |= 64
            ev = row_edited_event(self, 'EDITED_ROW', changed_index)
            self.dialog.app.send_events(ev)

    def sort(self, column_alias, modifiers):
        # TODO: find out if this should be a public function
        ev = table_header_event(
            self, column_alias, None, modifiers, 'HEADER_CLICK')
        self.dialog.app.send_events(ev)

    def _on_data_tab_dbl_click(self):
        # TODO: rename or inline this appropriately
        if self.action_name:
            action = self.dialog.components[self.action_name]
            if action:
                action.on_execute(self.id)
                return
        if 'EMPTY|' in self.supported_events:
            self.used_listeners_mask |= 64
            ev = action_event(self, None, self.id)
            self.dialog.app.send_events(ev)

    def _fire_action_command(self, command):
        if command + '|' in self.supported_events:
            self.used_listeners_mask |= 64
            ev = action_event(self, command, self.id)
            self.dialog.app.send_events(ev)

    def _delete_row(self):
        self.dialog.component_changes(self, False)
        self._fire_action_command('DELETE_ROW')

    def _insert_row(self):
        self.dialog.component_changes(self, False)
        self._fire_action_command('INSERT_ROW')

    def _control_button_row_count(self):
        self.dialog.component_changes(self, True)
        self._fire_action_command('ROW_COUNT')

    def _control_button_columns(self):
        self.dialog.component_changes(self, True)
        self._fire_action_command('SET_COLUMNS')

    def _control_button_sort(self):
        self.dialog.component_changes(self, True)
        self._fire_action_command('SET_SORTING')

    def _control_button_debug_info(self):
        self.dialog.component_changes(self, True)
        self._fire_action_command('DEBUG_INFO')

    def up_down_row(self, command):
        if not self.up_down_enabled: return
        if self._table_model_up_down(command):   # TODO
            self.up_downed_rows = True
            self.dialog.component_changes(self, False)

    def _on_edit_cell(self, send, alias, row_index):
        self.edited_cells = True
        self.dialog.component_changes(self, False)
        if not send: return
        if 'EDITED_CELL|' not in self.supported_events: return
        self.used_listeners_mask |= 64
        ev = cell_edited_event(self, 'EDITED_CELL', alias, row_index)
        self.dialog.app.send_events(ev)

    def button_num_code_click(self, alias, row_index, value):
        self.edit_cell(alias, row_index, value, _skip_event=True)

        self.edited_cells = True
        self.dialog.component_changes(self, False)
        if 'BUTTON_NUM_CODE|' not in self.supported_events: return
        self.used_listeners_mask |= 64
        ev = cell_edited_event(self, 'BUTTON_NUM_CODE', alias, row_index)
        self.dialog.app.send_events(ev)

    def changed_properties(self):
        cdata = ['<root>']

        if self.selection_changed or self.active_index_changed:
            cdata.append("<selection{}>".format(" invertedSelection='true'" if self.inverted_selection else ""))
            cdata.append("<activeIndex>{}</activeIndex>".format(
                -1 if self.cursor_row_index is None else self.cursor_row_index))
            cdata.append("<selectedIndexes>{}</selectedIndexes>".format(','.join(map(str, self.selected_row_indexes))))
            cdata.append("</selection>")
            if self.selected_column_alias:
                cdata.append("<selectedColumnAlias>{}</selectedColumnAlias>".format(self.selected_column_alias))
            self.selection_changed = False
            # TODO: AIS doesn't do it, but we should probably unset active_index_changed too

        if self.headers_changed:
            cdata.append("<columns>")
            for column in self.columns:
                cdata.append("<column shortname='{}' width='{}'></column>".format(column.alias, column.width))
            cdata.append("</columns>")
            self.headers_changed = False

        if self.scrolled_vertically:
            cdata.append("<visibleBuffers>{}</visibleBuffers>".format(
                ','.join(map(str, range(self.num_visible_buffers)))))
            cdata.append("<loadedBuffers>{}</loadedBuffers>".format(
                ','.join(map(str, sorted(self.loaded_buffers)))))
            self.scrolled_vertically = False

        if self.edited_cells:
            cdata.append("<editedCells>")
            for alias, row_index in self.changed_cells:
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
                cdata.append("<cell row='{}' alias='{}' type='{}'>{}</cell>".format(row_index, alias, type, value))
            cdata.append("</editedCells>")
            self.changed_cells.clear()
            self.last_changed_row_index = None
            self.edited_cells = False

        if self.deleted_rows or self.up_downed_rows:
            cdata.append("<upDownedRows>{}</upDownedRows>".format(self._get_rows_ids()))   # TODO
            self._table_model_reset_rows_ids()
            self.deleted_rows = False
            self.up_downed_rows = False

        cdata.append("</root>")

        properties = {}
        properties['dataView'] = (True, True, ''.join(cdata))
        properties['editMode'] = (False, False, False)

        if self.status_visible_changed:
            properties['statusVisible'] = (False, False, self.status_visible)
            self.status_visible_changed = False

        if self.row_numbers_visible_changed:
            properties['rowNumbersVisible'] = (False, False, self.row_numbers_visible)
            self.row_numbers_visible_changed = False

        return self._build_changed_properties(**properties)

    def _ais_setDataView(self, id, body):
        data_view = body.find(id=id)
        if not data_view.contents: return
        if data_view.find(id='columnModel'):
            self._init_from_data_view(data_view)
        else:
            self._update_data(data_view)
    _ais_setDataView.wants_body = True

    def _update_data(self, data_view):
        self._update_selection_model_properties(data_view)

        data_tab_bodies = data_view.find(id='dataTabBodies')
        data_tab_bodies_fixed = data_view.find(id='dataTabBodiesFixed')
        if not data_tab_bodies: return

        self._update_data_tab_bodies_properties(data_view)
        self._update_data_position_properties(data_view)

        data_send_type = data_tab_bodies.get('datasendtype', 'update')
        if data_send_type == 'info':
            self.log('table', 'Updating info in {}'.format(self.id))
            return

        if data_tab_bodies.find(id='dataTabTmp'):
            if data_tab_bodies.thead:
                raise AISParseError("Unsupported thead in dataTabTmp")
            if not data_tab_bodies.tbody:
                data_send_type = 'update'
            self._load_rows(data_tab_bodies, data_tab_bodies_fixed,
                            replace=(data_send_type == 'update'))

        self._load_edit_models(data_view.find(id='dataTabEditModels'))

    def _load_rows(self, data_tab_bodies, data_tab_bodies_fixed, replace=True):
        really_replaced = replace and self.loaded_rows
        if replace:
            self.loaded_buffers = set()
            self.loaded_rows = []
            self.num_visible_buffers = 0

        for tbody in data_tab_bodies.find_all('tbody'):
            id = int(tbody['id'][len('dataTabBody'):])
            self.loaded_buffers.add(id)
            if self.num_visible_buffers < id + 1:
                self.num_visible_buffers = id + 1

        fixed_trs = {}
        if data_tab_bodies_fixed:
            for tr in data_tab_bodies_fixed.find_all('tr'):
                fixed_trs[tr['id']] = tr

        new_rows = {}
        for tr in data_tab_bodies.find_all('tr'):
            id = int(tr['id'][len('row_'):])
            rid = tr['rid']
            tds = tr.find_all('td')
            if data_tab_bodies_fixed:
                tds = fixed_trs[tr['id']].find_all('td') + tds
            cells = [self._load_cell(td) for td in tds]
            new_rows[id] = [cell.value for cell in cells]
            row = Row(id, rid, cells, self)

            while len(self.loaded_rows) <= row.id:
                self.loaded_rows.append(None)
            self.loaded_rows[row.id] = row

        self.log('table', 'Loaded {} rows in {}{}'.format(
            len(new_rows), self.id,
            ' (replacing old content)' if really_replaced else ''),
            new_rows)

    def _load_cell(self, td):
        value = td.get_text()
        if value == '\xa0': value = ''

        if td.get('datatype') == 'boolean':
            value = bool(td.find(class_='booleanCellChecked'))

        if td.get('datatype') == 'image':
            value = td.img['src']

        checkbox = td.find('input', type='checkbox')
        if checkbox:
            return Cell(
                value=bool(checkbox.get('checked')), title=None,
                edited_by='checkBox', combo_box_mode=None, model=None,
                send_edit_cell=checkbox.get('sendeditcell', 'false') == 'true',
                disabled=checkbox.get('disabled', 'false') == 'true')

        return Cell(
            value=value, title=td.get('title'), edited_by=td.get('editedby'),
            combo_box_mode=td.get('cbmode'), model=td.get('model'),
            send_edit_cell=td.get('sendeditcell', 'false') == 'true',
            disabled=td.get('disabled', 'false') == 'true')

    def _load_edit_models(self, data_tab_edit_models):
        if not data_tab_edit_models: return

        self.combobox_options = {}

        for select in data_tab_edit_models.find_all('select'):
            options = self.combobox_options[select['id']] = []
            for index, option in enumerate(select.find_all('option')):
                options.append(Option(
                    title=option.get_text(),
                    id=option['sid'],
                    tool_tip_text=option['title'],
                ))

    def scroll_down(self, buffers=1):
        if self.is_end_of_data: return
        self.log('action', 'Scrolling down in {}'.format(self.id))
        self.num_visible_buffers += buffers
        self.scrolled_vertically = True
        self.dialog.component_changes(self, True)
        ev = cursor_event(self, 'pagedown', 'PAGEDOWN')
        self.dialog.app.send_events(ev)

    def all_rows(self):
        if self.declared_row_count > 0:
            self.scroll_down(self.declared_row_count // self.buffer_size + 1)

        while not self.is_end_of_data:
            self.scroll_down(10)
        if self.truncated:
            raise AISBehaviorError("AIS did not return all table rows")
        return self.loaded_rows

    def select(self, indexes, cursor=None, inverted=False, column_alias=None, *, _skip_event=False):
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
                raise TypeError('column_alias is None')
            if len(indexes) != 1:
                raise ValueError('must specify exactly one row index')
        else:
            if column_alias is not None:
                raise TypeError('column_alias is not None')

        if inverted and not (self.multiple_selection and self.select_all_enabled):
            raise ValueError('inverted selection not supported for this table')
        if len(indexes) > 1 and not self.multiple_selection:
            raise ValueError('multiple selection not supported for this table')
        if self.always_selected and ((not inverted and len(indexes) == 0) or
                (inverted and len(indexes) == len(self.loaded_rows))):
            raise ValueError('empty selection not supported for this table')

        self.log('action', 'Selecting {}{}{} {}{} in {}'.format(
            'column {} of '.format(column_alias) if column_alias else '',
            'inverted ' if inverted else '',
            'rows' if len(indexes) > 1 else 'row',
            ', '.join(map(str, indexes)),
            ' with cursor at {}'.format(cursor) if indexes != [cursor] else '',
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

        if was_multiple_selection != is_multiple_selection:
            self.dialog.try_interactive(self, "switchMultiple")

        if active_index_changed:
            self.active_index_changed = True
            self.dialog.component_changes(self, True)
            self._fire_action_command('ACTIVE_ROW_CHANGE')

        if selection_changed:
            self.selection_changed = True
            self.dialog.component_changes(self, True)

        if selection_changed and not _skip_event:
            evs = []
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
            self.dialog.app.send_events(*evs)

    def edit_cell(self, alias, row_index, value, *, _skip_event=False):
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

        self.select(row_index,
            column_alias=(alias if self.cell_selection_mode else None),
            _skip_event=(is_checkbox and send_edit_cell))

        self.log('action', 'Setting cell {} of row {} in {} to {!r}'.format(
            alias, row_index, self.id, value))

        cell = row.cells[column.index] = cell._replace(value=value)

        self.changed_cells.add((alias, row_index))
        self.last_changed_row_index = row_index

        if not _skip_event:
            self._on_edit_cell(send_edit_cell, alias, row_index)
