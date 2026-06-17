from aisikl.typeutils import ct, nn
from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.context import Context


class PortalApp(NamedTuple):
    id: str
    title: str
    url: str
    description: str


async def get_modules(ctx: Context) -> list[tuple[str, list[tuple[str, list[PortalApp]]]]]:
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
    await ctx.log('portal', 'Opening main menu')
    front_soup = await ctx.request_html('/ais/portal/changeTab.do?tab=0')

    results: list[tuple[str, list[tuple[str, list[PortalApp]]]]] = []

    for menu_item in front_soup.find_all(class_='left-menu-item'):
        menu_link = nn(menu_item.find('a'))
        _, _, module = ct(str, menu_link['href']).partition('changeModul.do?modul=')
        if not module: continue

        await ctx.log('portal', f'Opening section "{menu_link.get_text()}"')
        applist_soup = await ctx.request_html(
            '/ais/portal/changeModul.do?modul=' + module)

        submodules: list[tuple[str, list[PortalApp]]] = []
        for submodule in applist_soup.find_all(class_='submodul'):
            apps: list[PortalApp] = []
            for app in submodule.find_all(class_='aplikacia'):
                app_link = nn(app.a)
                apps.append(PortalApp(
                    id=nn(app.find(class_='kod')).get_text(),
                    title=ct(str, app_link['title']),
                    url=ct(str, app_link['url']),
                    description=nn(app.find(class_='popis')).get_text().strip(),
                ))

            submodule_name = nn(submodule.find(class_='submodul-text')).get_text()
            submodules.append((submodule_name, apps))

        results.append((menu_link.get_text(), submodules))

    return results


async def get_apps(ctx: Context) -> dict[str, PortalApp]:
    '''Downloads the main menu of AIS and returns the visible applications.

    Args:
        ctx: The :class:`~aisikl.context.Context` to use.
    Returns:
        The dict of applications. Keys are applications IDs and values are
        objects with ``id``, ``url``, ``title`` and ``description``. The menu
        structure is not preserved.
    '''
    result: dict[str, PortalApp] = {}
    modules = await get_modules(ctx)
    for _module_name, submodules in modules:
        for _submodule_name, apps in submodules:
            for app in apps:
                result[app.id] = app
    return result
