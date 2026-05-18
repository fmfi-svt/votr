from anycorn.logging import Logger as AnycornLogger
import datetime as dt
import json
import logging
import os
from typing import ClassVar, TYPE_CHECKING, override

if TYPE_CHECKING:
    from collections.abc import Iterable
    from anycorn import Config as AnycornConfig
    from anycorn.typing import ResponseSummary, WWWScope


_pid = os.getpid()
_enable_color = os.isatty(2) and not os.getenv("NO_COLOR")


def _dict_headers(h: Iterable[tuple[bytes, bytes]]) -> dict[str, str]:
    return {k.decode("latin1"): v.decode("latin1") for k, v in h}


def _prefix(prefix: str, value: str | None) -> str:
    return prefix + value if value else ""


class VotrLogger(AnycornLogger):
    log_label: ClassVar[str | None] = None

    def __init__(self, config: AnycornConfig) -> None:  # pyright: ignore [reportMissingSuperCall]
        # Not calling super().__init__(). It configures "anycorn.error" badly:
        # the logger is given a handler, but also propagate = True. That's wrong
        # because if the root logger has handlers too, it causes double logging.

        # Main logging configuration.
        # Applies to "anycorn", "votrfront.*", and loggers in other libraries.
        # But not to "anycorn.access".
        logging.basicConfig(
            format=f"[%(asctime)s] [{_pid}{_prefix('/', self.log_label)}] [%(name)s] [%(levelname)s] %(message)s",
            level=config.loglevel,
        )

        # Unlike super().__init__, don't set its `handlers` or `propagate`.
        # Rename from "anycorn.error" to "anycorn".
        self.error_logger: logging.Logger | None = logging.getLogger("anycorn")

        # Unlike super().__init__, don't add a formatter.
        if isinstance(config.accesslog, str) and config.accesslog != "-":
            self.access_logger = logging.getLogger("anycorn.access")
            self.access_logger.setLevel("INFO")
            self.access_logger.propagate = False
            if not self.access_logger.hasHandlers():
                self.access_logger.addHandler(
                    logging.FileHandler(config.accesslog))
        else:
            self.access_logger = None

        self.access_log_format = config.access_log_format  # unused

        # httpx2 INFO is too noisy. Allow it only if the main loglevel is DEBUG.
        if config.loglevel == "INFO":
            logging.getLogger("httpx2").setLevel("WARNING")

    @override
    async def access(
        self,
        request: WWWScope,
        response: ResponseSummary | None,
        request_time: float,
    ) -> None:
        """Custom access log.

        Adds JSON, color, timestamp precision, and request["state"] fields.

        Probably a waste of time, given how rarely anyone reads the log...
        """
        request_headers = _dict_headers(request["headers"])
        response_headers = _dict_headers((response or {}).get("headers", []))
        response_status = (response or {}).get("status", None)

        if self.access_logger is not None:
            # Schema loosely inspired by OTel SemConv.
            payload = {
                "timestamp": dt.datetime.now(dt.UTC).astimezone().isoformat(),
                "client.address": (request.get("client") or [None])[0],
                "user.name": request["state"].get("votr_log_user"),
                "http.request.method_original": request.get("method"),
                "url.path": request["path"],
                "url.query": request["query_string"].decode("latin1"),
                "http.response.status_code": response_status,
                "votr.status": request["state"].get("votr_log_status"),
                "http.response.body.size": response_headers.get(
                    "content-length"),
                "http.request.header.referer": [request_headers.get("referer")],
                "user_agent.original": request_headers.get("user-agent"),
                "http.route": getattr(request.get("route"), "path", None),
                "votr.duration_s": request_time,
                "process.pid": _pid,
                "process.title": self.log_label,
            }
            self.access_logger.info("%s", json.dumps(payload))

        elif self.error_logger is not None:
            color = "32" if (response_status or 400) < 400 else "31"
            self.error_logger.info(  #
                "%s%s %s%s -> %s%s%s",
                f"\x1b[{color}m" if _enable_color else "",
                request.get("method") or "???",
                request["path"],
                _prefix("?", request["query_string"].decode("latin1")),
                response_status or "???",
                _prefix("+", request["state"].get("votr_log_status")),
                "\x1b[0m" if _enable_color else "",
            )


class VotrConfig:
    logger_class = VotrLogger

    # - `worker_class`, `workers`: are not used by anycorn.serve().
    # - `bind`, `root_path`, `accesslog`, `loglevel`: given in CLI options.
    # - `graceful_timeout`: not relevant in blue-green deployments.
    # - TODO: Revisit `max_requests`, `max_requests_jitter` if we leak memory.
