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

Votr's code base consists of three layers that build on each other. **Aisikl**,
the lowest layer, does the actual communication by sending HTTP requests with
fake user actions and parsing the responses from WebUI (the framework AIS2 is
based on). **Fladgejt** contains the business logic for various AIS2 tasks and
knows where to find which buttons and tables. And **Votrfront** is the web app
that Votr's users interact with.

## Development setup

- You need Linux. (macOS or WSL1 or WSL2 might work too. Nobody tried it.)
- _Optional step:_ [Install uv][uv].
- _Optional step:_ Install Python 3. Note that on Debian/Ubuntu you should
  install it with `sudo apt install python3-venv` because they separated "venv"
  into its own package. Also note that you don't need a system-wide `pip`.
- _Optional step:_ [Install Node.js][node.js]. Make sure it's a recent version.
  The official packages on Debian/Ubuntu are frequently very outdated, but you
  can try [NodeSource][], or per-user installation with [nvm][].
- _Optional step:_ [Install Yarn 1][yarn]. _Optional substep:_ Read [how to
  install it per-user without sudo][sudo].
- [Install Git][git].
- Download Votr source code using Git:
  ```shell
  git clone https://github.com/fmfi-svt/votr.git
  cd votr
  ```
- Download and set up dependencies:
  ```shell
  ./x install
  ```
  Rerun this every time you pull a new version of Votr, in case some
  dependencies were updated.<br> _Optional step:_ Add `--uv=local`,
  `--nodejs=local` and/or `--yarn=local` if you didn't install them system-wide,
  or if you just prefer to use an isolated local version. You may need to
  [install curl][curl]. (Behind the scenes, this downloads Python binaries from
  [python-build-standalone][pbs] and official Node.js binaries from nodejs.org.)
- To start a local Votr server, open two terminals and run these commands:
  ```shell
  ./x serve --debug
  ```
  ```shell
  ./x yarn watch
  ```

[uv]: https://docs.astral.sh/uv/getting-started/installation/
[node.js]: https://nodejs.org/en/download/package-manager/
[nodesource]: https://github.com/nodesource/distributions
[nvm]: https://github.com/nvm-sh/nvm
[yarn]: https://classic.yarnpkg.com/en/docs/install
[sudo]: https://stackoverflow.com/a/59227497
[git]: https://git-scm.com/download/linux
[curl]: https://everything.curl.dev/get
[pbs]: https://gregoryszorc.com/docs/python-build-standalone/main/

## Contributing to Votr

If you'd like to help improve Votr, please get in touch! E-mail us at
fmfi-svt@googlegroups.com and we'll help you with anything you need -- whether
it's [choosing a task](https://github.com/fmfi-svt/votr/issues) to work on,
understanding Votr's code, implementing your changes, or sending a pull request
on GitHub.

## Developer documentation

Some documentation is on the wiki: https://github.com/fmfi-svt/votr/wiki

Some documentation is in docstrings in the source code. You could build it with
Sphinx if you really wanted to read it in a browser.

Building documentation:

    uv run --with sphinx,sphinx-rtd-theme make -C docs html
