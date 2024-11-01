docker_image_name ?= commit-meter
docker_image_tag ?= v1.0.0

dockerfile_path = deploy/Dockerfile
registry_prefix ?= ''

build:
	docker build --build-arg USE_CHINA_MIRROR=true -f $(dockerfile_path) -t $(docker_image_name):$(docker_image_tag) .

build-nocache:
	docker build --build-arg USE_CHINA_MIRROR=true --no-cache -f $(dockerfile_path) -t $(docker_image_name):$(docker_image_tag) .

run:
	cd deploy && docker-compose -f docker-compose-dev.yaml up -d

down:
	cd deploy && docker-compose -f docker-compose-dev.yaml down

reset:
	-@git pull
	-@cd deploy && docker-compose -f docker-compose-dev.yaml down
	-@docker rmi ${docker_image_name}:${docker_image_tag} || true
	-@$(MAKE) build
	-@cd deploy && docker-compose -f docker-compose-dev.yaml up -d

pip:
	pip freeze > requirements.txt



.PHONY: build build-nocache run reset ddl down-dev