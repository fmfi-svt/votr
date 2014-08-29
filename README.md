
Votr
====

The next version of the Fajr project. Votr provides easier access to AIS2,
the academic information system used at Comenius University and many other
universities in Slovakia.

Votr consists of three layers that build on each other. **Votrfront** is the web
app that users interact with. **Fladgejt** contains the AIS-specific business
logic and knows where to find which buttons and tables. And **Aisikl** does the
actual communication by sending HTTP requests with fake mouse clicks and screen
scraping the responses from WebUI (the framework AIS is based on).

You will need Python 3 (with virtualenv) and Node.js (with npm).

Quick start:

    virtualenv3 venv
    source venv/bin/activate
    pip install beautifulsoup4 requests
    export AIS_COOKIE="your cosign-filter cookie value"
    python test1.py

Running the Votrfront web server:

    pip install werkzeug
    mkdir -p sessions logs
    export AIS_COOKIE="your cosign-filter cookie value"
    ./votrfront/buildstatic.sh --watch &
    python console.py serve --debug

Running IPython notebooks:

    pip install ipython[all]
    export AIS_COOKIE="your cosign-filter cookie value"
    ipython notebook

Building documentation:

    pip install sphinx sphinx-rtd-theme sphinxcontrib-napoleon
    make -C docs html

The HTML documentation is at <http://svt.fmph.uniba.sk/~tomi/votrdoc/>.
