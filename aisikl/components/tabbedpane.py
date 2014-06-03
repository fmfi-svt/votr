
from .control import Control
from aisikl.events import change_action_event


class TabbedPane(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.selected_index = int(element.get('selectedindex', '0'))

        self.panel_ids = []
        arena = element.find(id=element['id'] + 'Arena', recursive=False)
        for panel in arena.find_all(jsct=True, recursive=False):
            self.panel_ids.append(panel['id'])

    def _ais_setSelectedIndex(self, value):
        self.selected_index = int(value)

    def select(self, index):
        self.log('action', 'Switching {} to tab {}'.format(self.id, index))
        self.selected_index = index
        self._fire_event()

    def get_panel(self, index):
        return self.dialog.components[self.panel_ids[index]]
    def get_selected_panel(self):
        return self.get_panel(self.selected_index)

    def changed_properties(self):
        return self._build_changed_properties(
            selectedIndex=self.selected_index)

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        ev = change_action_event(self, self.selected_index)
        self.dialog.app.send_events(ev)
