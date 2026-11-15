.PHONY: all setup test build-store build-frontend run-api run-frontend

all: build-store test build-frontend

setup:
	pip install -r requirements.txt
	cd frontend && npm install

build-store:
	python scripts/build_official_store.py

test:
	python run_all_tests_suite.py

build-frontend:
	cd frontend && npm run build

run-api:
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev
