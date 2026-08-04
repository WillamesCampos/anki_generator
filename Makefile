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
