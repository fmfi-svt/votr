"""
See  https://github.com/fmfi-svt/votr/wiki/Production  for our reasons to use
anycorn.serve() instead of anycorn's own process supervisor, and various other
notes on Votr's production setup.
"""

from argparse import ArgumentParser, BooleanOptionalAction as BoolAction
import os
import signal
import subprocess
import sys
from typing import cast, NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from anycorn.typing import ASGIFramework


def concurrently(command1: list[str], command2: list[str]) -> NoReturn:
    p1 = subprocess.Popen(command1, stdin=subprocess.DEVNULL, process_group=0)
    p2 = subprocess.Popen(command2, stdin=subprocess.DEVNULL, process_group=0)
    interrupted = [False]

    def handle_sigint(signum: object, frame: object) -> None:
        interrupted[0] = True
        os.write(2, b"\nReceived SIGINT. Forwarding it to subprocesses.\n\n")
        os.killpg(p1.pid, signal.SIGINT)
        os.killpg(p2.pid, signal.SIGINT)

    signal.signal(signal.SIGINT, handle_sigint)
    os.waitid(os.P_ALL, 0, os.WEXITED | os.WNOWAIT)
    if not interrupted[0]:
        os.write(2, b"\nA subprocess exited unexpectedly. Cleaning up.\n\n")
        os.killpg(p1.pid, signal.SIGINT)
        os.killpg(p2.pid, signal.SIGINT)
    p1.wait()
    p2.wait()
    if interrupted[0]:
        # Don't show a KeyboardInterrupt-like traceback, but exit WIFSIGNALED.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.raise_signal(signal.SIGINT)
    sys.exit(1)


def cli(args: list[str]) -> None:
    parser = ArgumentParser()
    parser.add_argument("--bind", action="append")
    parser.add_argument("--debug", action=BoolAction, default=True)
    parser.add_argument("--static", action=BoolAction, default=True)
    parser.add_argument("--watch-js", action=BoolAction, default=True)
    parser.add_argument("--watch-py", action=BoolAction, default=True)
    parser.add_argument("--proxy-fix", action=BoolAction, default=False)
    parser.add_argument("--https", action=BoolAction, default=False)
    parser.add_argument("--root-path")
    parser.add_argument("--access-logfile")
    parser.add_argument("--error-logfile")
    parser.add_argument("--log-level")
    parser.add_argument("--log-label")

    options = parser.parse_args(args)

    if options.watch_js:
        concurrently(
            ["pnpm", "watch"],
            ["python3", "-Pm", "votrfront.serve", *args, "--no-watch-js"])

    if options.watch_py:
        from votrfront.base import ROOT_PATH

        cmd = [
            "watchmedo", "auto-restart",
            "--pattern=*.py",
            "--recursive",
            "--debounce-interval=0.5",
            # on import/syntax errors, don't retry until the next edit
            "--no-restart-on-command-exit",
            # just to optimize watched dirs: skip .venv and node_modules
            f"--directory={ROOT_PATH / "aisikl"}",
            f"--directory={ROOT_PATH / "fladgejt"}",
            f"--directory={ROOT_PATH / "votrfront"}",
            "--",
            "python3", "-Pm", "votrfront.serve", *args, "--no-watch-py",
        ]  # fmt: skip

        os.execvp(cmd[0], cmd)

    import anycorn
    import logging
    import trio
    from votrfront import local_settings
    from votrfront.anycorn_config import VotrConfig, VotrLogger
    from votrfront.app import build_app
    from votrfront.base import var_path

    os.makedirs(var_path('locks'), exist_ok=True)
    os.makedirs(var_path('logs'), exist_ok=True)
    os.makedirs(var_path('logdb'), exist_ok=True)
    os.makedirs(var_path('oldlogs'), exist_ok=True)
    os.makedirs(var_path('logarchive'), exist_ok=True)
    os.makedirs(var_path('sessions'), exist_ok=True)
    os.makedirs(var_path('reportlogs'), exist_ok=True)

    config = anycorn.Config.from_object(VotrConfig)
    config.bind = options.bind or ["127.0.0.1:5000"]
    if options.root_path:
        config.root_path = options.root_path
    if options.access_logfile:
        config.accesslog = options.access_logfile
    if options.log_level:
        config.loglevel = options.log_level
    if options.log_label:
        VotrLogger.log_label = options.log_label

    _ = config.log  # Force logger initialization a bit sooner, just in case.

    if options.https:
        if not var_path("ssl.crt").exists():
            subprocess.check_call([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                '-keyout', 'ssl.key', '-out', 'ssl.crt',
                '-sha256', '-days', '365', '-nodes', '-subj', '/CN=*',
            ], cwd=var_path())  # fmt: skip

        config.certfile = str(var_path("ssl.crt"))
        config.keyfile = str(var_path("ssl.key"))

    def reopen_log_files() -> None:
        for handler in logging.getLogger("anycorn.access").handlers:
            handler.close()
        if options.error_logfile:
            sys.stdout.flush()
            sys.stderr.flush()
            with open(options.error_logfile, "a") as f:
                os.dup2(f.fileno(), 1)
                os.dup2(f.fileno(), 2)

    reopen_log_files()

    app = build_app(
        settings=local_settings, debug=options.debug, static=options.static,
        proxy_fix=options.proxy_fix)

    async def handle_sigusr1() -> None:
        with trio.open_signal_receiver(signal.SIGUSR1) as signal_aiter:
            async for _signum in signal_aiter:
                await config.log.info("Caught SIGUSR1, reopening log files")
                reopen_log_files()

    async def shutdown_trigger() -> None:
        with trio.open_signal_receiver(signal.SIGTERM) as signal_aiter:
            async for _signum in signal_aiter:
                await config.log.info("Caught SIGTERM, shutting down")
                return

    async def body() -> None:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(handle_sigusr1)

            await anycorn.serve(  # pyright: ignore [reportUnknownMemberType]
                cast("ASGIFramework", app),
                config,
                shutdown_trigger=shutdown_trigger,
            )

            nursery.cancel_scope.cancel()

    trio.run(body)


if __name__ == "__main__":
    cli(sys.argv[1:])
