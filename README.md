
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

You will need Python 3 (with virtualenv and python3-dev headers) and Node.js
(with npm).

Quick start:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements.txt
    ./console.py serve --debug

Sourcing `activate` adds `venv/bin` to your PATH. You could also directly call
`venv/bin/pip ...` and `venv/bin/python console.py ...` instead.

Running IPython notebooks:

    pip install ipython[all]
    export AIS_COOKIE="your cosign-filter cookie value"
    ipython notebook

Building documentation:

    pip install sphinx sphinx-rtd-theme sphinxcontrib-napoleon
    make -C docs html

The HTML documentation is at <http://svt.fmph.uniba.sk/~tomi/votrdoc/>.
