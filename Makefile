COMPOSE_RUN_TOOLING = docker compose -f docker-compose.tooling.yml run tooling

help:	## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

checkformatting:	## Checks code formatting
	$(COMPOSE_RUN_TOOLING) scripts/checkformatting

