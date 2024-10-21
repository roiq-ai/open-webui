RYE := $(shell command -v rye 2> /dev/null)
BACKEND := $(shell pwd)/backend
AWS_ACCOUNT=875668830489
AWS_REGION=us-east-1
ECR := 875668830489.dkr.ecr.us-east-1.amazonaws.com/roiqai-service
TAG := $(shell git rev-parse --abbrev-ref HEAD)

ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

bump-version:
	$(RYE) version -b minor

format:
	$(RYE) run  black .
	$(RYE) run autoflake . --recursive --remove-unused-variables --in-place \
	--ignore-init-module-imports --remove-all-unused-imports --exclude ".venv/|/venv/"

.PHONY: login
login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com

.PHONY: build
build:
	docker build -t open-webui .  --platform linux/amd64

.PHONY: push
push: bump-version build
	docker tag open-webui ${ECR}:${TAG}
	docker push ${ECR}:${TAG}

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