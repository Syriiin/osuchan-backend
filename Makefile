ENV ?= dev
UID = $(shell id -u)
GID = $(shell id -g)
COMPOSE_RUN_TOOLING = UID=${UID} GID=${GID} docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.tooling.yml run --rm --build tooling
COMPOSE_APP_DEV = docker compose -f docker-compose.yml -f docker-compose.override.yml

help:	## Show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

env: 	## Switch to an environment config
	@mkdir -p config/active
	cp config/${ENV}/*.env config/active/

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

shell:	## Opens python shell in django project
	$(COMPOSE_RUN_TOOLING) python manage.py shell

psql:	## Opens psql
	$(COMPOSE_RUN_TOOLING) python manage.py dbshell

createsuperuser:	## Creates new super user
	$(COMPOSE_RUN_TOOLING) python manage.py createsuperuser

resetdb:	## Resets the database
	$(COMPOSE_RUN_TOOLING) sh -c "python manage.py sqlflush | python manage.py dbshell"

test:	## Runs test suite
	$(COMPOSE_RUN_TOOLING) coverage run -m pytest --ignore data

test-coverage-report:	## Get test coverage report
	$(COMPOSE_RUN_TOOLING) sh -c "coverage report -m && coverage html"

build-dev:	## Builds development docker images
	$(COMPOSE_APP_DEV) build

start-dev:	## Starts development environment
	$(COMPOSE_APP_DEV) up -d

clean-dev:	## Cleans development environment
	$(COMPOSE_APP_DEV) down --remove-orphans
