III_BIN ?= iii
III_ENGINE_DIR ?= ../iii-engine
III_PID_FILE ?= /tmp/iii-engine.pid
III_LOG_FILE ?= /tmp/iii-engine.log
III_ENGINE_DATA ?= /tmp/iii-engine-data

III_CONFIG_NODE = packages/node/iii/tests/fixtures/config-test.yaml
III_CONFIG_SHARED = .github/engine-config/test-config.yml

.PHONY: help engine-build engine-start engine-stop engine-status engine-logs engine-clean
.PHONY: setup setup-node setup-python
.PHONY: lint lint-node lint-python lint-rust
.PHONY: test test-node test-python test-rust
.PHONY: integration integration-node integration-python integration-rust
.PHONY: ci ci-node ci-python ci-rust

help:
	@echo "III SDK Developer Makefile"
	@echo ""
	@echo "Engine management:"
	@echo "  engine-build     Build engine from source"
	@echo "  engine-start     Start engine (requires III_CONFIG, III_HEALTH_PORT)"
	@echo "  engine-stop      Stop engine"
	@echo "  engine-status    Check if engine is running"
	@echo "  engine-logs      Tail engine log file"
	@echo "  engine-clean     Remove engine data, logs, and PID file"
	@echo ""
	@echo "Setup:"
	@echo "  setup            Install deps for all SDKs"
	@echo "  setup-node       pnpm install"
	@echo "  setup-python     uv sync in packages/python/iii"
	@echo ""
	@echo "Lint:"
	@echo "  lint             Lint all SDKs"
	@echo "  lint-node        Biome + tsc"
	@echo "  lint-python      Ruff + mypy"
	@echo "  lint-rust        cargo fmt + clippy"
	@echo ""
	@echo "Tests (engine must be running):"
	@echo "  test             Run all SDK tests"
	@echo "  test-node        Node.js tests"
	@echo "  test-python      Python tests"
	@echo "  test-rust        Rust tests"
	@echo ""
	@echo "Integration (start engine, test, stop):"
	@echo "  integration      Run all integration tests"
	@echo "  integration-node integration-python integration-rust"
	@echo ""
	@echo "CI-like (build engine + integration):"
	@echo "  ci               Build engine, run all integration tests"
	@echo "  ci-node ci-python ci-rust"
	@echo ""
	@echo "Variables (override with VAR=value):"
	@echo "  III_BIN          Engine binary path or alias (default: iii)"
	@echo "  III_ENGINE_DIR   Engine source dir for engine-build (default: ../iii-engine)"
	@echo ""
	@echo "Examples:"
	@echo "  make ci-node III_ENGINE_DIR=../iii-engine"
	@echo "  make integration"
	@echo "  make integration-rust III_BIN=/path/to/iii"

engine-build:
	@echo "Building III engine in $(III_ENGINE_DIR)..."
	@cd "$(III_ENGINE_DIR)" && cargo build --release
	@echo "Engine built at $(III_ENGINE_DIR)/target/release/iii"

engine-start:
	@test -n "$(III_CONFIG)" || { echo "error: III_CONFIG is required (e.g. make engine-start III_CONFIG=path/to/config.yml III_HEALTH_PORT=49134)"; exit 1; }
	@test -n "$(III_HEALTH_PORT)" || { echo "error: III_HEALTH_PORT is required (e.g. make engine-start III_CONFIG=path/to/config.yml III_HEALTH_PORT=49134)"; exit 1; }
	@$(MAKE) engine-stop 2>/dev/null || true
	@pid=$$(lsof -ti :$(III_HEALTH_PORT) 2>/dev/null); [ -z "$$pid" ] || { kill -9 $$pid 2>/dev/null || true; sleep 2; }
	@rm -rf "$(III_ENGINE_DATA)"
	@mkdir -p "$(III_ENGINE_DATA)"
	@cp "$(CURDIR)/$(III_CONFIG)" "$(III_ENGINE_DATA)/config.yml"
	@ENGINE_BIN="$(III_BIN)"; \
		case "$$ENGINE_BIN" in /*) ;; *) ENGINE_BIN="$(CURDIR)/$$ENGINE_BIN";; esac; \
		cd "$(III_ENGINE_DATA)" && $$ENGINE_BIN --config config.yml > "$(III_LOG_FILE)" 2>&1 & echo $$! > "$(III_PID_FILE)"
	@echo "Waiting for III Engine on port $(III_HEALTH_PORT)..."
	@for i in $$(seq 1 30); do \
		if nc -z 127.0.0.1 $(III_HEALTH_PORT) 2>/dev/null; then \
			echo "III Engine is ready!"; exit 0; \
		fi; \
		echo "  attempt $$i/30..."; sleep 2; \
	done; \
	echo "Engine did not become ready. Logs:"; tail -n 50 "$(III_LOG_FILE)" || true; exit 1

engine-stop:
	@if [ -f "$(III_PID_FILE)" ]; then \
		kill "$$(cat $(III_PID_FILE))" 2>/dev/null || true; \
		rm -f "$(III_PID_FILE)"; \
		echo "Engine stopped"; \
	else \
		echo "No engine PID file found"; \
	fi

engine-status:
	@if [ -f "$(III_PID_FILE)" ] && kill -0 "$$(cat $(III_PID_FILE))" 2>/dev/null; then \
		echo "Engine is running (PID $$(cat $(III_PID_FILE)))"; \
	else \
		echo "Engine is not running"; exit 1; \
	fi

engine-logs:
	@tail -f "$(III_LOG_FILE)"

engine-clean:
	@rm -rf "$(III_ENGINE_DATA)"
	@rm -f "$(III_LOG_FILE)" "$(III_PID_FILE)"
	@echo "Engine data cleaned"

setup: setup-node setup-python

setup-node:
	@cd packages/node && pnpm install

setup-python:
	@cd packages/python/iii && uv sync --extra dev

lint: lint-node lint-python lint-rust

lint-node:
	@npx @biomejs/biome check packages/node
	@cd packages/node && pnpm --filter iii-sdk exec tsc --noEmit

lint-python:
	@cd packages/python/iii && uv run ruff check src && uv run mypy src

lint-rust:
	@cd packages/rust/iii && cargo fmt --all -- --check
	@cd packages/rust/iii && cargo clippy --all-targets --all-features -- -D warnings

test: test-node test-python test-rust

test-node:
	@cd packages/node && pnpm --filter iii-sdk test

test-python:
	@cd packages/python/iii && uv run pytest -q

test-rust:
	@cd packages/rust/iii && cargo test --all-features --quiet

integration-node:
	@$(MAKE) engine-start III_CONFIG="$(III_CONFIG_NODE)" III_HEALTH_PORT=49199
	@trap '$(MAKE) engine-stop' 0 1 2 3 15; \
		III_BRIDGE_URL=ws://localhost:49199 III_HTTP_URL=http://localhost:3199 $(MAKE) test-node

integration-python:
	@$(MAKE) engine-start III_CONFIG="$(III_CONFIG_SHARED)" III_HEALTH_PORT=49134
	@trap '$(MAKE) engine-stop' 0 1 2 3 15; \
		III_BRIDGE_URL=ws://localhost:49134 III_HTTP_URL=http://localhost:3199 $(MAKE) test-python

integration-rust:
	@$(MAKE) engine-start III_CONFIG="$(III_CONFIG_SHARED)" III_HEALTH_PORT=49134
	@trap '$(MAKE) engine-stop' 0 1 2 3 15; \
		III_BRIDGE_URL=ws://localhost:49134 III_HTTP_URL=http://localhost:3199 $(MAKE) test-rust

integration: integration-node integration-python integration-rust

ci-node: engine-build
	@$(MAKE) integration-node III_BIN="$(III_ENGINE_DIR)/target/release/iii"

ci-python: engine-build
	@$(MAKE) integration-python III_BIN="$(III_ENGINE_DIR)/target/release/iii"

ci-rust: engine-build
	@$(MAKE) integration-rust III_BIN="$(III_ENGINE_DIR)/target/release/iii"

ci: engine-build
	@$(MAKE) integration III_BIN="$(III_ENGINE_DIR)/target/release/iii"
