MANAGE=python manage.py

install-dep:
	python -m pip install -r requirements.txt

run:
	$(MANAGE) runserver

run-glob: 
	$(MANAGE) runserver 0.0.0.0:8000

migrate:
	$(MANAGE) migrate

createsuperuser: 
	$(MANAGE) createsuperuser

prod: 
	uvicorn adsoft.asgi:application --reload

prod-glob:
	uvicorn adsoft.asgi:application --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +