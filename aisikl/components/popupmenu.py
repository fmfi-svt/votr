
from aisikl.events import component_event
from .control import Control


class PopupMenu(Control):
    def show(self):
        # Some menus emit an "init" event when opened. You can do that with
        # this function, but you must do it manually when needed. By default,
        # menu items can be accessed directly without opening the menu first.
        self.log('action', 'Opening {}'.format(self.id))
        ev = component_event(self, 'init', 'INIT')
        self.dialog.app.send_events(ev)

    def hide(self):
        # Some menus emit a "beforeclose" event when closed. You can do that
        # with this function, but you must do it manually when needed. By
        # default, menus do not need to be opened and closed explicitly.
        self.log('action', 'Closing {}'.format(self.id))
        ev = component_event(self, 'beforeclose', 'BEFORECLOSE')
        self.dialog.app.send_events(ev)
