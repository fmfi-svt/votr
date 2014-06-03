
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
    front_soup = ctx.request_html('/ais/portal/changeTab.do?tab=0')

    results = []

    for menu_item in front_soup.find_all(class_='left-menu-item'):
        menu_link = menu_item.find('a')
        _, _, module = menu_link['href'].partition('changeModul.do?modul=')
        if not module: continue

        ctx.log('portal', 'Opening section "{}"'.format(menu_link.get_text()))
        applist_soup = ctx.request_html(
            '/ais/portal/changeModul.do?modul=' + module)

        submodules = []
        for submodule in applist_soup.find_all(class_='submodul'):
            apps = []
            for app in submodule.find_all(class_='aplikacia'):
                app_link = app.a
                apps.append(PortalApp(
                    id=app.find(class_='kod').get_text(),
                    title=app_link['title'],
                    url=app_link['url'],
                    description=app.find(class_='popis').get_text().strip(),
                ))

            submodule_name = submodule.find(class_='submodul-text').get_text()
            submodules.append((submodule_name, apps))

        results.append((menu_link.get_text(), submodules))

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
