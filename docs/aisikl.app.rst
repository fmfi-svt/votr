Application
===========

.. automodule:: aisikl.app
    :members:
    :undoc-members:
    :exclude-members: Operation, Update

    .. class:: Operation(target, method, args)

        Record of a "big" action done by AIS that isn't handled automatically
        and requires some reaction, such as:

        - Opening a new application or browser window
        - Showing a message box or another modal dialog
        - Opening and closing dialogs

        You can use :meth:`Application.collect_operations` to express that you
        expected something to happen and are prepared to handle it, or use
        :attr:`Application.ignored_messages` to specify that some ``messageBox``
        Operations can be safely ignored. If an Operation isn't collected or
        safely ignored, it throws an exception.

        .. attribute:: target

            The target JavaScript object. Either "webui" or "dm". Usually,
            you just need :attr:`method`.

        .. attribute:: method

            The type of the operation -- the name of the WebUI JavaScript
            method being called. See :data:`known_operations` for possible
            values.

        .. attribute:: args

            The list of attributes to the JavaScript method. Votr follows the
            same signatures as WebUI. For example, if ``op.method ==
            "openDialog"``, the Votr call is ``app.open_dialog(*op.args)``.

    .. class:: Update(dialog, target, method, args)

        Record of AIS calling a setter on some component.

        .. attribute:: dialog

            The dialog name.

        .. attribute:: target

            The target component name.

        .. attribute:: method

            The setter method that is called. In Votr, this original method
            name will be prefixed with ``_ais_``.

        .. attribute:: args

            The list of setter arguments. (Usually a single string.)
