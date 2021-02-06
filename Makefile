# Directory containing the application to run
CODE := airtasker_challenge

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
	pipenv run black ${CODE}
	pipenv run mypy ${CODE}

.PHONY: test
test: lint
	pipenv run pytest
