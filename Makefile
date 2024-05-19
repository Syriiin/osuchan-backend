ENV ?= dev
UID = $(shell id -u)
GID = $(shell id -g)
COMPOSE_RUN_TOOLING = UID=${UID} GID=${GID} docker compose -f compose.yaml -f compose.override.yaml -f compose.tooling.yaml run --rm --build tooling
COMPOSE_APP_DEV = docker compose -f compose.yaml -f compose.override.yaml

help:	## Show this help
	@printf "\nUSAGE: make [command] \n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf " \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@printf '\n'

env:	## Switch to an environment config
	@mkdir -p config/active
	rm -rf config/active/*
	cp -r config/${ENV}/* config/active/

bash:	## Opens bash shell in tooling container
	$(COMPOSE_RUN_TOOLING) bash

checkformatting:	## Checks code formatting
	$(COMPOSE_RUN_TOOLING) scripts/checkformatting

fixformatting:	## Fixes code formatting
	$(COMPOSE_RUN_TOOLING) scripts/fixformatting

checkmigrations:	## Checks for missing migrations
	$(COMPOSE_RUN_TOOLING) python manage.py makemigrations --check

makemigrations:	## Generates migrations
	$(COMPOSE_RUN_TOOLING) python manage.py makemigrations

migrate:	## Runs migrations
	$(COMPOSE_RUN_TOOLING) python manage.py migrate

shell:	## Opens python shell in django project
	$(COMPOSE_RUN_TOOLING) python manage.py shell

psql:	## Opens psql
	$(COMPOSE_RUN_TOOLING) python manage.py dbshell

createsuperuser:	## Creates new super user
	$(COMPOSE_RUN_TOOLING) python manage.py createsuperuser

resetdb:	## Resets the database
	$(COMPOSE_RUN_TOOLING) sh -c "python manage.py sqlflush | python manage.py dbshell"

test:	## Runs test suite
	$(COMPOSE_RUN_TOOLING) coverage run -m pytest

test-coverage-report:	## Get test coverage report
	$(COMPOSE_RUN_TOOLING) sh -c "coverage report -m && coverage html"

collectstatic:	## Collect static files
	$(COMPOSE_RUN_TOOLING) python manage.py collectstatic --no-input

build-dev:	## Builds development docker images
	$(COMPOSE_APP_DEV) build

start-dev: build-dev	## Starts development environment
	$(COMPOSE_APP_DEV) up -d

clean-dev:	## Cleans development environment containers
	$(COMPOSE_APP_DEV) down --remove-orphans

reset-dev:	## Resets config, data and containers to default states
	make env ENV=dev
	$(COMPOSE_RUN_TOOLING) python manage.py flush --no-input
	$(COMPOSE_APP_DEV) down --remove-orphans --volumes
	make start-dev
