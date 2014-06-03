
from .control import Control


class ActionableControl(Control):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.action_name = element.get('actionname')

    @property
    def action(self):
        if not self.action_name: return None
        return self.dialog.components[self.action_name]

    def try_execute_action(self):
        # TODO: This isn't used in webui, but we might replace
        # tryExecuteActionForElement() with it.
        if self.action:
            self.action.execute(self.id)
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
