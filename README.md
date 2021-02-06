# Airtasker challenge

Hello, world.

## Installation

This repository uses [Pipenv](https://pipenv.pypa.io/en/latest/) to install
dependencies and run the project.

In order to install it, please run:

    $ pip install --user pipenv

If `pip` is not installed on your machine, the following should be enough to
install it:

    $ sudo easy_install pip


TODO: Dockerfile


## Running

Running the application can be done via

    $ make run

This will ensure that dependencies are installed and up-to-date before running
the application.


The codebase comes with a suite of unit tests, which can be run via

    $ make test


This will also run a couple of lint/format stages.

* [black](https://github.com/psf/black), a code formatter for Python.
* [mypy](https://github.com/python/mypy), a static type checker for Python.

These stages can also be run on their own via:

    $ make lint
