
from .component import Component


class Control(Component):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.read_only = element.get('_readonly', 'false') == 'true'
        self.tab_order = int(element.get('tabindex', '0'))
        self.tool_tip_text = element.get('title')

    def is_really_enabled(self):
        return super().is_really_enabled() and self.parent.is_really_enabled()

    def _ais_setReadOnly(self, value):
        self.read_only = (value == 'true')
    def _ais_setTabOrder(self, value):
        self.tab_order = int(value)
    def _ais_setToolTipText(self, value):
        self.tool_tip_text = value

    def _ais_setX(self, value): pass
    def _ais_setY(self, value): pass
    def _ais_setWidth(self, value): pass
    def _ais_setHeight(self, value): pass
    def _ais_setPastWidth(self, value): pass
    def _ais_setPastHeight(self, value): pass
    def _ais_setForeground(self, value): pass
    def _ais_setBackground(self, value): pass
    def _ais_setComponentStyle(self, value): pass
    def _ais_setFontSize(self, value): pass
    def _ais_setFontStyle(self, value): pass

    def changed_properties(self):
        return ''

    def _build_changed_properties(self, **kwargs):
        # TODO: This could be shorter.
        result = []
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

    def update_value_interactives(self, type):
        pass # TODO

    # TODO: We need a method to explicitly request firing a blur event.
    # (Find out which classes can fire it in webui.)
