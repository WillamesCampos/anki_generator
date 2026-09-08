.PHONY: up down logs migrate makemigrations run seed test frontend-install frontend-dev frontend-build frontend-lint frontend-test patch minor major

CURRENT_VERSION := $(shell git describe --tags --match "v[0-9]*.[0-9]*.[0-9]*" --abbrev=0 2>/dev/null || echo v0.0.0)

define bump
	@test -z "$$(git status --porcelain)" || (echo "Working tree sujo — commit ou stash antes de dar release." && exit 1)
	@git fetch origin main --quiet
	@[ "$$(git rev-parse HEAD)" = "$$(git rev-parse origin/main)" ] || (echo "HEAD local diferente de origin/main — dê pull/push antes." && exit 1)
	@if git rev-parse $(CURRENT_VERSION) >/dev/null 2>&1; then \
		git diff --quiet $(CURRENT_VERSION) -- CHANGELOG.md && (echo "CHANGELOG.md não mudou desde $(CURRENT_VERSION) — atualize antes de taguear." && exit 1) || true; \
	fi
	@NEW_VERSION=$$(echo $(CURRENT_VERSION) | sed 's/^v//' | awk -F. -v part=$(1) '{ \
		major=$$1; minor=$$2; patch=$$3; \
		if (part == "major") { major++; minor=0; patch=0 } \
		else if (part == "minor") { minor++; patch=0 } \
		else { patch++ } \
		print "v" major"."minor"."patch }'); \
	echo "Atual: $(CURRENT_VERSION)  ->  Nova: $$NEW_VERSION"; \
	read -p "Confirma criar e enviar a tag $$NEW_VERSION? [y/N] " ok; \
	[ "$$ok" = "y" ] || exit 1; \
	git tag -a "$$NEW_VERSION" -m "Release $$NEW_VERSION"; \
	git push origin "$$NEW_VERSION"
endef

patch:
	$(call bump,patch)

minor:
	$(call bump,minor)

major:
	$(call bump,major)

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	poetry -C django run python manage.py migrate

makemigrations:
	poetry -C django run python manage.py makemigrations

run:
	poetry -C django run python manage.py runserver

seed:
	poetry -C django run python manage.py seed_decks --reset

test:
	poetry -C django run pytest apps/

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm test
