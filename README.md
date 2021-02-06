# Airtasker challenge

Hello, world.

## Installation

This repository uses [Pipenv](https://pipenv.pypa.io/en/latest/) to install
dependencies and run the project.

### docker-compose (recommended)

There is a [docker-compose.yml](docker-compose.yml) file that allows to install dependencies and run the application in one single command.

    $ make docker-compose-run

Please make sure that you have `docker-compose` installed (it should be
installed alongiide docker on MacOS). Otherwise, please refer to the
[documentation](https://docs.docker.com/compose/install/).

This will:

- Build a Docker container with the application
- Run a sidecar memcache container (used as a backing store to ensure multiple
  clients/workers can share the rate limiter).
- Run both containers
- The rate-limited endpoint can be reached via `http://0.0.0.0:5000/`

Example:

```
>> curl http://0.0.0.0:5000/
Hello, world!
```

To tear the application down, please run

    $ make docker-compose-down

### Local installation

In order to install the application locally, you will need pipenv. Please run:

    $ pip install --user pipenv

If `pip` is not installed on your machine, the following should be enough to
install it:

    $ sudo easy_install pip

### Docker installation

Alternately, there are Makefile targets to build and run a dockerised version
of the project. To build a Docker image, please run:

    $ make cook-image

This will build the project, the resulting image will be tagged
`airtasker-challenge`.

## Running

### Running locally

Running the application locally can be done via

    $ make run

This will ensure that dependencies are installed and up-to-date before running
the application.

By default, an in-memory rate-limiter will be used (multiple instances will not
share the rate limiter). `memcache` can be used to share the rate limiter:

    $ export STORE_BACKEND=memcache
    $ export MEMCACHE_CONNECTION_STRING=<memcache host:memcache port>  # e.g: 0.0.0.0:11211
    $ make run

### Running in Docker

Running the application in a docker container can be done via

    $ make docker-run

This will build the container if it had not previously been built.

By default, an in-memory rate-limiter will be used (multiple instances will not
share the rate limiter). `memcache` can be used to share the rate limiter:

    $ docker run -e STORE_BACKEND=memcache -e MEMCACHE_CONNECTION_STRING=<memcache host:memcache port> -t airtasker-challenge

## Tests

The codebase comes with a suite of unit tests, which can be run via

    $ make test


This will also run a couple of lint/format stages.

* [black](https://github.com/psf/black), a code formatter for Python.
* [mypy](https://github.com/python/mypy), a static type checker for Python.

These stages can also be run on their own via:

    $ make lint

## Design

To mention:
* memcache error = do not rate limit (return {} and 0). conscious trade-off:
  issues with infra should not impact users. risk for underlying services
* going further: could fall-back to MemoryStore upon errors
