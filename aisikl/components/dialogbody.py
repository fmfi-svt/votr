from aisikl.components.component import Component


class DialogBody(Component):
    """The dialog's ``<body>`` element.

    Votr's ``DialogBody`` is vestigial. The ``DialogBody`` class in webui.js
    mostly handles DOM manipulation, which isn't needed in Votr, and the few
    useful bits were moved to [`Dialog`][aisikl.dialog.Dialog].
    """

    def _ais_setWidth(self, value: object) -> None: pass
    def _ais_setHeight(self, value: object) -> None: pass
    def _ais_setFocusedComponent(self, value: object) -> None: pass
