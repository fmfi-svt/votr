
Votr
====

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

Installing and running Votr
---------------------------

System requirements:

*   Install Python 3.4+ and virtualenv. E.g. on Ubuntu 18.04: `sudo apt install
    virtualenv`
*   Install [node.js 8+][1]. E.g. on Ubuntu 18.04: `sudo apt install nodejs`
    *   If your Linux distribution doesn't have node.js >= 8, or if you don't
        want to install node.js system-wide, you can use nvm or nodeenv.
        [Read more.][2]
*   [Install Yarn.][3]

[1]: https://nodejs.org/en/download/package-manager/
[2]: https://github.com/fmfi-svt/votr/wiki/Installation-options
[3]: https://yarnpkg.com/en/docs/install

Download and set up Votr:

```shell
git clone https://github.com/fmfi-svt/votr.git
cd votr
virtualenv -p python3 venv
```

Install Votr's dependencies in `votr/venv` and `votr/node_modules`:

```shell
venv/bin/pip install -r requirements.txt
yarn install
```

(Note: Repeat this step every time you pull a new version of Votr, in case they
were updated.)

Run Votr by starting these two commands in separate terminals: \
(They are Votr's web server and Votr's JS/CSS build system.)

```shell
venv/bin/python console.py serve --debug
```

```shell
yarn watch
```

Contributing to Votr
--------------------

If you'd like to help improve Votr, please get in touch! E-mail us at
fmfi-svt@googlegroups.com and we'll help you with anything you need -- whether
it's [choosing a task](https://github.com/fmfi-svt/votr/issues) to work on,
understanding Votr's code, implementing your changes, or sending a pull request
on GitHub.

Developer documentation
-----------------------

Some documentation is on the wiki: https://github.com/fmfi-svt/votr/wiki

Some documentation is in docstrings in the source code and rendered with Sphinx:
http://svt.fmph.uniba.sk/~tomi/votrdoc/

Building documentation:

    pip install sphinx sphinx-rtd-theme
    make -C docs html
