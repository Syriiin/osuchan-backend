UID = $(shell id -u)
GID = $(shell id -g)
COMPOSE_RUN_TOOLING = UID=${UID} GID=${GID} docker compose -f docker-compose.tooling.yml run --rm tooling
COMPOSE_RUN_API = UID=${UID} GID=${GID} docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm api

help:	## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

checkformatting:	## Checks code formatting
	$(COMPOSE_RUN_TOOLING) scripts/checkformatting

fixformatting:	## Fixes code formatting
	$(COMPOSE_RUN_TOOLING) scripts/fixformatting

makemigrations:	## Generates migrations
	$(COMPOSE_RUN_API) python manage.py makemigrations
