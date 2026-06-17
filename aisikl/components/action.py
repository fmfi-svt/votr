from aisikl.events import action_event
from aisikl.components.actionlist import ActionList
from aisikl.components.component import Component, is_true
from aisikl.typeutils import ct, ct_none
from typing import TYPE_CHECKING, cast, override

if TYPE_CHECKING:
    from aisikl.components.button import Button
    from aisikl.components.menuitem import MenuItem
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Action(Component):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        if parent_id is not None: raise TypeError('expected None')
        if element is not None: raise TypeError('expected None')
        self.accessible = ct(bool, properties.get('accessible', True))
        self.tool_tip_text = ct_none(str, properties.get('toolTipText'))
        # We only ever saw shortcut==None, but webui calls toUpperCase().
        self.shortcut = ct_none(str, properties.get('sc'))
        self.action_list_id = ct_none(str, properties.get('actionListId'))
        # We only ever saw confirm_question==None, but webui calls confirm().
        self.confirm_question = ct_none(str, properties.get('confirmQuestion'))
        self.component_ids: list[str] = ct(list, properties.get('cids') or [])

    def get_action_list(self) -> ActionList | None:
        if self.action_list_id is None: return None
        return ct_none(ActionList, self.dialog.components.get(self.action_list_id))

    def get_components(self) -> list[Component]:
        return [self.dialog.components[id] for id in self.component_ids]

    def get_buttons_and_menu_items(self) -> list[Button | MenuItem]:
        return [cast('Button | MenuItem', o) for o in self.get_components()
                if o.component_type in ('button', 'menuItem')]

    async def execute(self, original_source_name: str | None=None, params: str | None=None) -> None:
        '''Executes the action and emits the appropriate event.'''
        if not (self.accessible and self.enabled and self.enabled_in_ui and
                self.visible and self.visible_in_ui):
            # TODO: we should return here, but we can only do that once we
            # properly support interactives. for now, the developer knows best.
            pass

        if not original_source_name:
            await self.log('action', f'Executing {self.id}')

        ev = action_event(self, None, original_source_name or self.id, params)
        # TODO: We should technically ask confirm_question before firing
        # (if ev.listening is True), but we probably don't care.
        await self.dialog.app.send_events(ev)

    def _ais_setAccessible(self, value: object) -> None:
        self.accessible = is_true(value)
    @override
    def _ais_setVisibleInUI(self, value: object) -> None:
        super()._ais_setVisibleInUI(value)
        for o in self.get_buttons_and_menu_items():
            o._ais_setVisibleInUI(value)
    @override
    def _ais_setEnabledInUI(self, value: object) -> None:
        super()._ais_setEnabledInUI(value)
        for o in self.get_buttons_and_menu_items():
            o._ais_setEnabledInUI(value)
    @override
    def _ais_setTitle(self, value: object) -> None:
        for o in self.get_buttons_and_menu_items():
            if o.title == self.title:
                o._ais_setTitle(value)
        super()._ais_setTitle(value)
    def _ais_setToolTipText(self, value: object) -> None:
        for o in self.get_buttons_and_menu_items():
            if o.tool_tip_text == self.tool_tip_text:
                o._ais_setToolTipText(value)  # pyright: ignore [reportPrivateUsage]
        self.tool_tip_text = ct_none(str, value)
    def _ais_setConfirmQuestion(self, value: object) -> None:
        for o in self.get_buttons_and_menu_items():
            if o.confirm_question == self.confirm_question:
                o._ais_setConfirmQuestion(value)  # pyright: ignore [reportPrivateUsage]
        self.confirm_question = ct_none(str, value)
