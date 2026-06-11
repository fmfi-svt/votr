
from __future__ import annotations
import json
import re
from .exceptions import AISParseError
from .components import component_classes
from aisikl.events import component_event
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.app import Application
    from aisikl.components.component import Component
    from aisikl.components.control import Control

_properties_re = re.compile(r'^var componentsProperties\s*=\s*(.*);$')

class Dialog:
    '''An opened AIS dialog.

    The dialog's components can be accessed as items of the ``components``
    dict, or directly as attributes of the dialog object. That is, ``dlg.x ==
    dlg.components["x"]``.

    Attributes:
        name: The identifier of this dialog instance.
        title: The user-visible dialog title.
        code: The identifier of the AIS dialog class (probably).
        parent_dialog_name: Name of the dialog that opened us.
        modal: Whether the dialog prevents access to others while opened.
        is_main_dialog: whether it's the top level body of the application.
        closeable: Whether the dialog can be closed.
        hide_title_bar: Whether AIS would show the title row.
        app: The :class:`aisikl.app.Application` this dialog belong to.
        components: The dict of components present in the dialog.
    '''

    def __init__(self, name: str, title: str, code: str, parent_dialog_name: str | None, modal: bool,
                 is_main_dialog: bool, closeable: bool, hide_title_bar: bool, app: Application) -> None:
        self.name = name
        self.title = title
        self.code = code
        self.parent_dialog_name = parent_dialog_name
        self.modal = modal
        self.is_main_dialog = is_main_dialog
        self.closeable = closeable
        self.hide_title_bar = hide_title_bar
        self.app = app

        self.components = {}
        self.changed_components = None

    def _init(self, url: str) -> None:
        '''Load the dialog body.

        Called from :meth:`aisikl.app.Application.open_dialog`.
        '''
        dialog_soup = self.app.ctx.request_html(url)
        self.app.ctx.log('benchmark', 'Begin dialog initialization')

        body = dialog_soup.body
        first_element_child = body.find(True)
        scripts = dialog_soup.find_all('script')
        if not (body.get('id') == self.name and
                'jsct' not in body and
                'dialogBody' in body.get('class', []) and
                first_element_child and
                first_element_child.get('id') == 'dialogComponentsArea' and
                scripts):
            raise AISParseError("Unexpected dialog body response")

        self.components = {}
        self.changed_components = None

        last_line = scripts[-1].string.strip().split('\n')[-1].strip()
        match = _properties_re.match(last_line)
        if not match:
            raise AISParseError("Couldn't find dialog componentProperties")
        component_properties = json.loads(match.group(1))

        elements = { e['id']: e for e in dialog_soup.find_all(id=True) }
        if 'dt_selection' in elements or 'dt_selection_area' in elements:
            raise AISParseError("#dt_selection is not supported")

        for id, properties in component_properties.items():
            if properties.get('tmp'): continue
            if id == 'suggestionsArea': continue

            element = elements.get(id)
            parent_id = None
            if element:
                parent = element.find_parent(
                    lambda p: p.get('id') in component_properties)
                if parent:
                    parent_id = parent['id']

            type = properties.get('t')
            if type not in component_classes:
                raise AISParseError("Unsupported component type: %r" % type)
            component = component_classes[type](
                self, id, type, parent_id, properties, element)

            self.components[id] = component

        self.body = self.components[self.name]

        self.app.ctx.log('benchmark', 'End dialog initialization')

    def __getattr__(self, name: str) -> Component:
        if 'components' in self.__dict__ and name in self.components:
            return self.components[name]
        raise AttributeError(name)

    def __dir__(self):
        return super().__dir__() + list(self.components)

    def changed_properties(self) -> str:
        '''Return the <changedProperties> string for this dialog.'''
        # We ignore width, height, x, y, focusedComponent and dtSelection.
        # So there are no <nameValue> pairs, only <embObjChProps>.
        if self.changed_components is None: return ''
        result = (
            '<changedProperties><objName>' + self.name + '</objName>\n' +
            '<embObjChProps>\n' +
            ''.join(self.components[id].changed_properties()
                    for id in self.changed_components) +
            '</embObjChProps>\n' +
            '</changedProperties>\n')
        self.changed_components = None
        return result

    def try_interactive(self, component: Component, type: str) -> None:
        # Moved from DocumentBody. TODO: document that.

        pass # TODO

    def component_changes(self, component: Control, is_minor: bool) -> None:
        # Moved from DocumentBody. TODO: document that.

        # TODO: Eventual support for ChangeGuardInteractive goes here.
        # (is_minor decides whether to set elementsChanged or not.)

        if self.changed_components is None:
            # Use dict instead of set as it has consistent iteration order in
            # Python 3.7+, unlike set. (https://stackoverflow.com/q/3848091)
            # The server seems to accept any order, but being deterministic is
            # occasionally handy when inspecting or comparing log files.
            #
            # In theory changed_components == {} means only the dialog itself
            # has changed, and None means no change at all. But Votr ignores
            # Dialog properties, and never calls component_changes(None, ...).
            self.changed_components = {}

        if component:
            self.changed_components[component.id] = True
            self.try_interactive(component, 'change')

    def click_close_button(self) -> None:
        if not self.closeable:
            raise ValueError("Dialog {} has no close button".format(self.name))
        # TODO: Return unless "self.enabled" is True.

        self.app.ctx.log('action',
            'Pressing close button of {}'.format(self.name))
        ev = component_event(self.body, 'close', 'CLOSE')
        self.app.send_events(ev)
