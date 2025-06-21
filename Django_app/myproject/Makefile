.PHONY: help dev prod migrate test docker-up docker-down tailwind-build tailwind-watch

help:
	@echo "Available commands:"
	@echo "  dev         - Run development server"
	@echo "  prod        - Run production server locally"
	@echo "  migrate     - Run migrations (dev)"
	@echo "  migrate-prod - Run migrations (prod)"
	@echo "  test        - Run tests"
	@echo "  tailwind-build - Build Tailwind CSS"
	@echo "  tailwind-watch - Watch Tailwind CSS changes"
	@echo "  docker-up   - Start Docker containers"
	@echo "  docker-down - Stop Docker containers"

dev:
	python manage.py runserver

prod:
	python manage_prod.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

migrate-prod:
	python manage_prod.py makemigrations
	python manage_prod.py migrate

test:
	python manage.py test

tailwind-build:
	python manage.py tailwind build

tailwind-watch:
	python manage.py tailwind start

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down