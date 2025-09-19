# Variables
PYTHON=python3
MANAGE=$(PYTHON) manage.py

install: ## Install dependencies
	$(PYTHON) -m pip install -r requirements.txt

run: ## Run Django development server
	$(MANAGE) runserver

run-glob: ## Run Django development server
	$(MANAGE) runserver 0.0.0.0:8000

migrate: ## Apply database migrations
	$(MANAGE) migrate

createsuperuser: ## Create an admin user
	$(MANAGE) createsuperuser

prod: 
	uvicorn adsoft.asgi:application --reload

prod-glob:
	uvicorn adsoft.asgi:application --reload --host 0.0.0.0 --port 8000

clean: ## Remove pycache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +