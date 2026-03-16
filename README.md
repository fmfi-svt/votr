# Votr

Votr is an alternative frontend providing easier access to AIS2, the academic
information system used at many universities in Slovakia. If you are a student
of Comenius University, you can try Votr at https://votr.uniba.sk. If you need
help, write to us at fmfi-svt@googlegroups.com. If you're interested in the
development of Votr, read on.

AIS2 doesn't have an official API, so Votr primarily uses web scraping. The AIS2
servers think they're talking to a real user with a real web browser pressing
buttons and navigating the endless popup windows that form AIS2's user
interface. But it is in fact Votr, sending simulated button presses and parsing
AIS2's mangled tag soup.

Votr's codebase consists of three layers that build on each other. **Aisikl**,
the lowest layer, does the actual communication by sending HTTP requests with
fake user actions and parsing the responses from AVC WebUI (the framework AIS2
is based on). **Fladgejt** contains the business logic for various AIS2 tasks
and knows where to find which buttons and tables. And **Votrfront** is the web
app that Votr's users interact with.

## Development setup

- **You need Linux.** (macOS or WSL1 or WSL2 might work too. Nobody tried it.)
- **[Install Git](https://git-scm.com/download/linux)** if you don't have it.
- **[Install curl](https://everything.curl.dev/install/linux.html)** if you
  don't have it.
- Optional:
  **[Install uv](https://docs.astral.sh/uv/getting-started/installation/).**
  Alternatively, add `--uv=local` to the install command below instead.
- Optional: **Install Python 3.** Alternatively, just do nothing and uv will
  download it locally.
  - On Debian/Ubuntu, it's best to install `python3-venv`, not just `python3`.
    You probably don't need `pip`.
- Optional: **[Install Node.js](https://nodejs.org/en/download).**
  Alternatively, add `--nodejs=local` to the install command below instead.
  - The Debian/Ubuntu `nodejs` package is often too old. You could try
    [NodeSource](https://github.com/nodesource/distributions) or
    [nvm](https://github.com/nvm-sh/nvm).
- Optional: **[Install pnpm](https://pnpm.io/installation).** Alternatively, add
  `--pnpm=local` to the install command below instead.
- **Download Votr source code** using Git:
  ```shell
  git clone https://github.com/fmfi-svt/votr.git
  cd votr
  ```
- **Install our dependencies:** (options can be added here)
  ```shell
  ./x install
  ```
  Run it again every time you pull a new version of Votr.
- **Start a local Votr server:**
  ```shell
  ./x -W watch-and-serve --debug
  ```

## Contributing to Votr

If you'd like to help improve Votr, please get in touch! E-mail us at
fmfi-svt@googlegroups.com and we'll help you with anything you need -- whether
it's [choosing a task](https://github.com/fmfi-svt/votr/issues) to work on,
understanding Votr's code, implementing your changes, or sending a pull request
on GitHub.

## Developer documentation

Some documentation is on the wiki: https://github.com/fmfi-svt/votr/wiki

Some documentation is in docstrings in the source code. `./x build-docs` can be
used to generate a browsable HTML version, such as it is.
