
from .control import Control
from aisikl.events import action_event


class Panel(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.tab_id = element.get('tabId')
        self.title = element.get('name')
        self.autoscrolls = element.get('autoscrolls', 'false') == 'true'
        self.stacked = element.get('stacked', 'false') == 'true'
        self.collapsable = element.get('collapsable', 'false') == 'true'
        self.collapsed = element.get('collapsed', 'false') == 'true'

    def _ais_setCollapsed(self, value):
        self.collapsed = (value == 'true')

    def toggle_collapsed(self):
        if not self.collapsable: return
        if not self.parent.is_really_enabled(): return
        self.log('action', '{} {}'.format(
            'Opening' if self.collapsed else 'Closing', self.id))
        self.collapsed = not self.collapsed
        self._fire_event()

    def _fire_event(self):
        self.dialog.component_changes(self, False)
        command = 'COLLAPSE' if self.collapsed else 'EXPAND'
        ev = action_event(self, command, self.id)
        self.dialog.app.send_events(ev)

    def changed_properties(self):
        return self._build_changed_properties(collapsed=self.collapsed)
