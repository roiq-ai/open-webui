RYE := $(shell command -v rye 2> /dev/null)
BACKEND := $(shell pwd)/backend
AWS_ACCOUNT=875668830489
AWS_REGION=us-east-1
ECR := ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/open-webui

ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

format:
	$(RYE) format

.PHONY: login
login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com

.PHONY: build
build:
	docker build -t open-webui --no-cache . --platform linux/amd64

.PHONY: push
push: build login
	docker tag open-webui:latest ${ECR}:latest
	docker push ${ECR}:latest

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