RYE := $(shell command -v rye 2> /dev/null)
BACKEND := $(shell pwd)/backend

ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

format:
	$(RYE) run black $(BACKEND)/
	$(RYE) run isort --profile black $(BACKEND)/
	$(RYE) run autoflake -i -r --ignore-init-module-imports \
	--remove-all-unused-imports --remove-unused-variables $(BACKEND)

install:
	$(DOCKER_COMPOSE) up -d

remove:
	@chmod +x confirm_remove.sh
	@./confirm_remove.sh

start:
	$(DOCKER_COMPOSE) start
startAndBuild: 
	$(DOCKER_COMPOSE) up -d --build

stop:
	$(DOCKER_COMPOSE) stop

update:
	# Calls the LLM update script
	chmod +x update_ollama_models.sh
	@./update_ollama_models.sh
	@git pull
	$(DOCKER_COMPOSE) down
	# Make sure the ollama-webui container is stopped before rebuilding
	@docker stop open-webui || true
	$(DOCKER_COMPOSE) up --build -d
	$(DOCKER_COMPOSE) start

.PHONY: test
test:
	$(RYE) run pytest $(BACKEND)/test