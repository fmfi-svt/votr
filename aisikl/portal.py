
from collections import namedtuple

__all__ = ['get_modules', 'get_apps']


PortalApp = namedtuple('PortalApp', ['id', 'title', 'url', 'description'])


def get_modules(ctx):
    '''Downloads the main menu of AIS and return the list of modules.

    The separate pages of the main menu are called "modules", and the sections
    shown on one page are "submodules".

    Args:
        ctx: The :class:`~aisikl.context.Context` to use.
    Returns:
        The list of modules. Every module is returned as a
        ``(name, submodules)`` tuple, every submodule is returned as a
        ``(name, apps)`` tuple, and every app is an object with ``id``,
        ``url``, ``title`` and ``description``.
    '''
    ctx.log('portal', 'Opening main menu')
    front_html = ctx.request_html('/ais/portal/changeTab.do?tab=0')

    results = []

    for menu_item in front_html.find_class('left-menu-item'):
        menu_link = menu_item.find('.//a')
        _, _, module = menu_link.attrib['href'].partition('changeModul.do?modul=')
        if not module: continue

        ctx.log('portal', f'Opening section "{menu_link.only_text()}"')
        applist_html = ctx.request_html(
            '/ais/portal/changeModul.do?modul=' + module)

        submodules = []
        for submodule in applist_html.find_class('submodul'):
            apps = []
            for app in submodule.find_class('aplikacia'):
                app_link = app.find('.//a')
                apps.append(PortalApp(
                    id=app.find_class('kod')[0].only_text(),
                    title=app_link.attrib['title'],
                    url=app_link.attrib['url'],
                    description=app.find_class('popis')[0].only_text().strip(),
                ))

            submodule_name = submodule.find_class('submodul-text')[0].only_text()
            submodules.append((submodule_name, apps))

        results.append((menu_link.only_text(), submodules))

    return results


def get_apps(ctx):
    '''Downloads the main menu of AIS and returns the visible applications.

    Args:
        ctx: The :class:`~aisikl.context.Context` to use.
    Returns:
        The dict of applications. Keys are applications IDs and values are
        objects with ``id``, ``url``, ``title`` and ``description``. The menu
        structure is not preserved.
    '''
    result = {}
    modules = get_modules(ctx)
    for module_name, submodules in modules:
        for submodule_name, apps in submodules:
            for app in apps:
                result[app.id] = app
    return result
