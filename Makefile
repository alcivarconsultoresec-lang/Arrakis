.PHONY: install run test lint docker-up docker-down

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	python -m unittest discover -s tests -v

lint:
	python -m compileall app

docker-up:
	cp -n .env.example .env || true
	docker compose up --build

docker-down:
	docker compose down
