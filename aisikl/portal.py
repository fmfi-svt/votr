"""Functions for listing applications in the AIS portal UI (the old AIS
interface's main menu).

Warning:
    It's recommended to use ``aisikl.portal`` only in development (e.g. in
    IPython notebooks), but avoid it in production. It is surprisingly slow.
    Application URLs don't change over time, so it's better to find the URL once
    and hardcode it, rather than getting the URL from the portal every time you
    want to open it.
"""

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
    """Downloads the main menu of AIS and return the list of modules.

    The separate pages of the main menu are called "modules", and the sections
    shown on one page are "submodules".

    Returns:
        A list of modules. Every module is a tuple of (module name, list of
            submodules). Every submodule is a tuple of (submodule name, list of
            [`PortalApp`][]s).
    """
    await ctx.log("portal", "Opening main menu")
    front_soup = await ctx.parse_html(
        await ctx.request_ais("/ais/portal/changeTab.do?tab=0"))

    results: list[tuple[str, list[tuple[str, list[PortalApp]]]]] = []

    for menu_item in front_soup.find_all(class_="left-menu-item"):
        menu_link = nn(menu_item.find("a"))
        _, _, module = ct(str, menu_link["href"]).partition("changeModul.do?modul=")
        if not module: continue

        await ctx.log("portal", f'Opening section "{menu_link.get_text()}"')
        applist_soup = await ctx.parse_html(await ctx.request_ais(
            "/ais/portal/changeModul.do?modul=" + module))

        submodules: list[tuple[str, list[PortalApp]]] = []
        for submodule in applist_soup.find_all(class_="submodul"):
            apps: list[PortalApp] = []
            for app in submodule.find_all(class_="aplikacia"):
                app_link = nn(app.a)
                apps.append(PortalApp(
                    id=nn(app.find(class_="kod")).get_text(),
                    title=ct(str, app_link["title"]),
                    url=ct(str, app_link["url"]),
                    description=nn(app.find(class_="popis")).get_text().strip(),
                ))

            submodule_name = nn(submodule.find(class_="submodul-text")).get_text()
            submodules.append((submodule_name, apps))

        results.append((menu_link.get_text(), submodules))

    return results


async def get_apps(ctx: Context) -> dict[str, PortalApp]:
    """Downloads the main menu of AIS and returns the visible applications.
    Menu structure is not preserved.

    Returns:
        A dict of [`PortalApp`][]s keyed by application ID.
    """
    result: dict[str, PortalApp] = {}
    modules = await get_modules(ctx)
    for _module_name, submodules in modules:
        for _submodule_name, apps in submodules:
            for app in apps:
                result[app.id] = app
    return result
