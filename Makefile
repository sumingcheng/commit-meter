docker_image_name ?= commit-meter
docker_image_tag ?= v1.0.0

dockerfile_path = deploy/Dockerfile
registry_prefix ?= ''

# 安装uv（如果未安装）
install-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}

# uv相关命令
sync: install-uv
	uv sync

sync-dev: install-uv
	uv sync --extra dev

lock: install-uv
	uv lock

add: install-uv
	uv add $(PACKAGE)

add-dev: install-uv
	uv add --dev $(PACKAGE)

run-local: sync
	uv run python main.py

# Docker相关命令
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

# 清理
clean:
	rm -rf .venv
	rm -f uv.lock

.PHONY: install-uv sync sync-dev lock add add-dev run-local build build-nocache run reset ddl down-dev lint lint-fix format export-requirements clean