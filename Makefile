.PHONY: up down logs migrate makemigrations run seed test frontend-install frontend-dev frontend-build frontend-lint frontend-test

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
