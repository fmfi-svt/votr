from aisikl.components.component import Component, is_true
from aisikl.typeutils import ct, ct_none, nn, really_int
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from aisikl.dialog import Dialog
    from bs4.element import Tag


class Control(Component):
    def __init__(self, dialog: Dialog, id: str, type: str, parent_id: str | None, properties: dict[str, object], element: Tag | None) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        element = nn(element)
        self.parent_id = nn(parent_id)
        self.read_only = ct(bool, properties.get('ro', False))
        self.tab_order = int(ct(str, element.get('tabindex', '0')))
        self.tool_tip_text = ct_none(str, element.get('title'))

    @property
    def parent(self) -> Component:
        return self.dialog.components[self.parent_id]

    @override
    def is_really_enabled(self) -> bool:
        return super().is_really_enabled() and self.parent.is_really_enabled()

    def _ais_setReadOnly(self, value: object) -> None:
        self.read_only = is_true(value)
    def _ais_setTabOrder(self, value: object) -> None:
        self.tab_order = really_int(value)
    def _ais_setToolTipText(self, value: object) -> None:
        self.tool_tip_text = ct_none(str, value)

    def _ais_setX(self, value: object) -> None: pass
    def _ais_setY(self, value: object) -> None: pass
    def _ais_setWidth(self, value: object) -> None: pass
    def _ais_setHeight(self, value: object) -> None: pass
    def _ais_setForeground(self, value: object) -> None: pass
    def _ais_setBackground(self, value: object) -> None: pass
    def _ais_setComponentStyle(self, value: object) -> None: pass
    def _ais_setFontSize(self, value: object) -> None: pass
    def _ais_setFontStyle(self, value: object) -> None: pass

    def changed_properties(self) -> str:
        return ''

    def _build_changed_properties(self, **kwargs: str | bool | tuple[bool | None, bool, str | bool]) -> str:
        # TODO: This could be shorter.
        result: list[str] = []
        write = result.append

        write("<changedProperties>")
        write("<objName>" + self.id + "</objName>")
        write("<propertyValues>")

        for name, value in kwargs.items():
            is_xml = use_cdata = False
            if isinstance(value, tuple): is_xml, use_cdata, value = value
            if isinstance(value, bool): value = 'true' if value else 'false'

            if use_cdata: value = "<![CDATA[" + value + "]]>"
            write("<nameValue>")
            write("<name>" + name + "</name>")
            if is_xml is not None:
                write("<isXml>" + str(bool(is_xml)).lower() + "</isXml>")
            write("<value>" + value + "</value>")
            write("</nameValue>")

        write("</propertyValues>")
        write("<embObjChProps isNull='true'/>")
        write("</changedProperties>")

        return ''.join(result)

    def update_value_interactives(self, type: str) -> None:
        pass # TODO

    # TODO: We need a method to explicitly request firing a blur event.
    # (Find out which classes can fire it in webui.)
