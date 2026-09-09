.PHONY: install run test clean

install:
	poetry install

run:
	poetry run python -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000 --no-access-log

stop:
	fuser -k 8000/tcp || true

restart: stop run

test:
	poetry run pytest

clean:
	rm -rf workspace/*
	rm -rf workspace__/*
	rm -rf artifacts/*
	find . -type d -name "__pycache__" -exec rm -rf {} +
