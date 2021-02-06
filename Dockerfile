FROM python:3.7-alpine

ENV FLASK_APP=airtasker_challenge.app

# Run the app on http://0.0.0.0:5000
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

# Install libmemcached to use pylibmc
RUN apk add --no-cache --virtual \
        .build-deps build-base libmemcached-dev linux-headers zlib-dev

RUN pip install pipenv

WORKDIR /code

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --system --deploy

COPY . .

USER nobody
CMD ["flask", "run"]
