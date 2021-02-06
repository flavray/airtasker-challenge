# Directory containing the application to run
CODE := airtasker_challenge

# Directory containing tests for the application
TEST_CODE := tests

# Tag for the local docker image
DOCKER_TAG := airtasker-challenge

# Expected the app.py file to be present in ${CODE}
FLASK_APP := ${CODE}.app

.PHONY: all
all: run

.PHONY: env
env:
	pipenv install

.PHONY: dev-env
dev-env:
	pipenv install --dev

.PHONY: run
run: env
	FLASK_APP=${FLASK_APP} pipenv run flask run

.PHONY: lint
lint: dev-env
	pipenv run black ${CODE} ${TEST_CODE}
	pipenv run mypy ${CODE} ${TEST_CODE}

.PHONY: test
test: lint
	pipenv run pytest

.PHONY: cook-image
cook-image:
	docker build -t ${DOCKER_TAG} .

.PHONE: docker-run
docker-run: cook-image
	docker run -p 5000:5000 ${DOCKER_TAG}
