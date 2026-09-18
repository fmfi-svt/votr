from pathlib import Path
from typing import Final, NotRequired, Protocol, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence
    from fladgejt.base import BaseClient
    from fladgejt.login import ServerDict
    from httpcore2 import AsyncConnectionPool
    from votrfront.login import OneLogin_Saml2_Settings


ROOT_PATH = Path(__file__).resolve().parent.parent


def var_path(*path_segments: Path | str) -> Path:
    return ROOT_PATH.joinpath('var', *path_segments)

    # NOTE: For future reference, if we later want to customize var_path within
    # unit tests, this should work:
    #     monkeypatch.setattr('votrfront.base.ROOT_PATH', tmp_path)
    #     (tmp_path / 'var').mkdir()


class Settings(Protocol):
    instance_id: Final[str]
    instance_title: Final[str]
    session_max_age: Final[int]
    root_url: Final[str | None]
    ua_code: Final[str | None]
    anketa_season: Final[str]
    anketa_end_ymd: Final[tuple[int, int, int]]
    feedback_link: Final[str]
    announcement_html: Final[str]
    servers: Final[Sequence[ServerDict]]


class VotrCookieLoggedIn(TypedDict):
    sessid: str


class VotrCookieLoggingIn(TypedDict):
    login_request_id: str
    server: str
    destination: str


class VotrCookieLoggedOut(TypedDict):
    pass


type VotrCookie = VotrCookieLoggedIn | VotrCookieLoggingIn | VotrCookieLoggedOut


class SessionDict(TypedDict):
    last_announcement: str
    csrf_token: str
    credentials: dict[str, object]
    client: BaseClient


class VotrState(TypedDict):
    connection_pool: AsyncConnectionPool
    saml_settings: OneLogin_Saml2_Settings | str
    settings: Settings
    votr_cookie_value: NotRequired[VotrCookie]
    votr_log_status: NotRequired[str]
    votr_log_user: NotRequired[str]


if TYPE_CHECKING:
    def _check_settings_type(s: Settings) -> None:
        pass

    import votrfront.default_settings as _default_settings
    import votrfront.local_settings as _local_settings

    _check_settings_type(_default_settings)
    _check_settings_type(_local_settings)
