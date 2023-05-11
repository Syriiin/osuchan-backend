ENV ?= template
UID = $(shell id -u)
GID = $(shell id -g)
COMPOSE_RUN_TOOLING = UID=${UID} GID=${GID} docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.tooling.yml run --build --rm tooling
COMPOSE_APP_DEV = docker compose -f docker-compose.yml -f docker-compose.override.yml

help:	## Show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

env: 	## Switch to an environment config
	@mkdir -p config/active
	cp config/${ENV}/*.env config/active/

checkformatting:	## Checks code formatting
	$(COMPOSE_RUN_TOOLING) scripts/checkformatting

fixformatting:	## Fixes code formatting
	$(COMPOSE_RUN_TOOLING) scripts/fixformatting

checkmigrations:	## Checks for missing migrations
	$(COMPOSE_RUN_TOOLING) python manage.py makemigrations --check

makemigrations:	## Generates migrations
	$(COMPOSE_RUN_TOOLING) python manage.py makemigrations

build-dev:	## Builds development docker images
	$(COMPOSE_APP_DEV) build

start-dev:	## Starts development environment
	$(COMPOSE_APP_DEV) up -d

clean-dev:	## Cleans development environment
	$(COMPOSE_APP_DEV) down --remove-orphans

test:	## Runs test suite
	$(COMPOSE_RUN_TOOLING) python -Wa manage.py test
