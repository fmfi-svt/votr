
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

Running Votr
------------

1.  Install Python 3.4+ and virtualenv. On recent Ubuntu or Debian, use:

        sudo apt install virtualenv

2.  Create a virtualenv directory. A virtualenv is an isolated environment that
    contains Python libraries, so that you don't have to install them
    system-wide, and each project can use different versions without conflicts.

        virtualenv -p python3 venv

3.  Activate the virtualenv. (Basically, this just adds `venv/bin` to your
    current shell's `$PATH`. Instead, you could just use `venv/bin/python`
    instead of `python`, `venv/bin/pip` instead of `pip`, etc.)

        source venv/bin/activate

4.  Install the latest version of `pip` (earlier versions don't support wheels),
    and then use it to install Python dependencies.

        pip install -U pip
        pip install -r requirements.txt

5.  Gather/build your CSS files:

        # copy pre-built CSS files to votrfront/static/
        ./votrfront/buildcss.sh setup
        # build the custom CSS
        ./votrfront/buildcss.sh
        # build the bootstrap custom base CSS - not needed in 99.99% cases
        ./votrfront/buildcss.sh bootstrap

6.  Install Node.js and npm/yarn. You can do so via
    [NVM](https://github.com/creationix/nvm). Follow instructions on the NVM
    website. After installing NVM, you may need to restart your
    terminal / source .bashrc . Afterwards, run:

        cd votrfront/js/
        nvm use
        npm i -g yarn
        yarn
        cd ../..

7.  Start the Javascript bundler (you will need to have this open in another
    terminal):

        cd votrfront/js
        yarn dev
        # for production build, do
        yarn build

8.  Start Votr. Remember to activate the virtualenv first if you haven't done it
    yet in this terminal.

        ./console.py serve --debug

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
