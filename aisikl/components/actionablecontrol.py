
from .control import Control


class ActionableControl(Control):
    def __init__(self, dialog, id, type, parent_id, properties, element):
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.action_name = properties.get('an')

    @property
    def action(self):
        if not self.action_name: return None
        return self.dialog.components[self.action_name]

    def try_execute_action(self, params=None):
        if self.action:
            self.action.execute(self.id, params)
            return True
        return False

    def is_really_enabled(self):
        return (super().is_really_enabled() and
                self.get_enabled_by_owner_container())

    def get_enabled_by_owner_container(self):
        action = self.action
        if not action: return True
        action_list = action.parent
        if not action_list: return True
        owner_container = action_list.owner_container
        if not owner_container: return True
        return owner_container.is_really_enabled()
