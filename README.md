# Airtasker challenge

Hello, world.


This repository contains an implementation of a rate-limiting module that stops
a particular requestor from making too many HTTP requests within a particular
period of time.


This module is written in Python.

## Installation

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

Example 2:

```
# Make 100 sequential calls to the API endpoint. They all succeed.
>> for i in `seq 100`; do curl --silent http://127.0.0.1:5000/ > /dev/null; done

# Subsequent calls fail.
>> curl http://0.0.0.0:5000/
Rate limit exceeded. Try again in #3595 seconds%

>> curl http://0.0.0.0:5000/
Rate limit exceeded. Try again in #788 seconds

# After more than 1h, calls succeed again.
>> curl http://0.0.0.0:5000/
Hello, world!
```

To tear the application down, please run

    $ make docker-compose-down

### Local installation

This repository uses [Pipenv](https://pipenv.pypa.io/en/latest/) to install
dependencies and run the project.

In order to install the application locally, you will need pipenv. Please run

    $ pip install --user pipenv

If `pip` is not installed on your machine, the following should be enough to
install it

    $ sudo easy_install pip

### Docker installation

Alternately, there are Makefile targets to build and run a dockerised version
of the project. To build a Docker image, please run

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
share the rate limiter). `memcache` can be used to share the rate limiter via

    $ make cook-image
    $ docker run -e STORE_BACKEND=memcache -e MEMCACHE_CONNECTION_STRING=<memcache host:memcache port> -p 5000:5000 -t airtasker-challenge

*Note: If memcache is running locally, memcache host needs to be your host's IP
address (or anything other than localhost, that can make it accessible).*

## Tests

The codebase comes with a suite of unit tests, which can be run via

    $ make test

This will also run a couple of lint/format stages.

* [black](https://github.com/psf/black), a code formatter for Python.
* [mypy](https://github.com/python/mypy), a static type checker for Python.

These stages can also be run on their own via

    $ make lint

## Code Structure

* The entrypoint to the application is located in
  [airtasker_challenge/app.py](airtasker_challenge/app.py).  This is a simple
  [Flask](https://flask.palletsprojects.com/en/1.1.x/) application, with a
  single endpoint (`/`).

The endpoint is rate-limited to 100 permits per hour, for every IP address, as
a cheap way to identify requestors. User identification could be done
differently (e.g: user api tokens) and easily plugged in the rate limiter.


* The rate limiter implementation is located in
  [airtasker_challenge/rate_limiter](airtasker_challenge/rate_limiter). It
  contains a Flask route decorator `@rate_limited` that is used to limit access
  to any Flask route (in our case, `/`).


* There is a test suite located in [tests/](tests/), which contains unit tests.


## Rate Limiter design

The rate limiter is bucketed, in 1-second buckets and uses a sliding window to
compute the number of acquisitions over the period of time configured (1h
here).

The implementation is backed by [memcache](https://memcached.org), to store and
distribute atomic counters. This means that multiple web workers can share the
rate limiter if they connect to the same memcache server(s). I could have used
Redis, a SQL database, or many other systems. memcached is simple to use and
deploy, with a lightweight client library.

I made the conscious decision to allow every request to pass if any issue with
memcache occurs (e.g: memcache is down, corrupted, etc...). The assumption is
that user experience should prevail, and running a rate limiter is a risk (to
allow "offenders" to over-use, and a risk to put any infrastructure under too
much load), but the risk of denying all requests from all users ("offender" or
not) seemed too high.
It is just a trade-off, and the implementation in
[airtasker_challenge/rate_limiter/store.py](airtasker_challenge/rate_limiter/store.py)
can easily be changed to return errors.

A further improvement could be to fallback to an in-memory store if anything
wrong occurred with memcache, and backoff from memcache for a few
(millis-)seconds.


As documented in
[airtasker_challenge/rate_limiter/rate_limiter.py](airtasker_challenge/rate_limiter/rate_limiter.py),
the buckets are 1-second long. This means that 3,600 keys need to be retrieved
from the store every time a request is made. Memcache is quite fast, but this
could become a bottleneck.

Ways to improve this could be to:

- Cache in-memory counters from buckets that are more than a couple of seconds
  old (there will be immutable)
- Increase the bucket duration (10 seconds? 1 minute? depends on the load).
  This will force to use approximations for the cooldown period, but reduce the
  number of keys to retrieve.


Configuration of the application (which store backend to use, memcache
connection string) is done via environment variables (`STORE_BACKEND`,
`MEMCACHE_CONNECTION_STRING`). This is easy to set and tweak both in a terminal
environment and a docker environment, and easy to read from the application.
This could have been a configuration file, but would have been less explicit
than environment variables.
