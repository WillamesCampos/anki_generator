db:
	docker run --name ankigen_db \
	-p 5432:5432 \
	-e POSTGRES_PASSWORD=ankigenerator \
	-e POSTGRES_DB=ankigen_db \
	-e POSTGRES_USER=anki \
	-d postgres:latest