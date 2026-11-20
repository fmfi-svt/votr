from typing import TYPE_CHECKING, Literal

from starlette.exceptions import HTTPException

if TYPE_CHECKING:
    from starlette.requests import Request

    from votrfront.base import VotrState


def fetch_metadata_debug_status(request: Request[VotrState]) -> str:
    """Returns a compact debug representation of fetch metadata headers."""
    return ":".join([
        request.headers.get("Sec-Fetch-Site", "~"),
        request.headers.get("Sec-Fetch-Mode", "~"),
        request.headers.get("Sec-Fetch-Dest", "~"),
        request.headers.get("Sec-Fetch-User", "~"),
        "cY" if request.headers.get("Cookie") else "cN",
    ])


def check_header(
    request: Request[VotrState],
    name: Literal["Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-Dest"],
    allowed_values: set[str],
) -> None:
    value = request.headers.get(name)
    if value is not None and value not in allowed_values:
        request.state["votr_log_status"] = (
            "badsecfetch:" + fetch_metadata_debug_status(request)
        )
        raise HTTPException(403, f"Unexpected {name} header value")
