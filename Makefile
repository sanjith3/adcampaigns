MANAGE=python manage.py

dep:
	python -m pip install -r requirements.txt

run:
	$(MANAGE) runserver

run-glob: 
	$(MANAGE) runserver 0.0.0.0:8000

migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

su: 
	$(MANAGE) createsuperuser

shell:
	$(MANAGE) shell

prod: 
	uvicorn adsoft.asgi:application --reload

prod-glob:
	uvicorn adsoft.asgi:application --reload --host 0.0.0.0 --port 8000

clean:
	pwsh -NoProfile -Command "Get-ChildItem -Path . -Recurse -Directory -Name '__pycache__' | ForEach-Object { Remove-Item -Path \$$_.FullName -Recurse -Force -ErrorAction SilentlyContinue }"
	pwsh -NoProfile -Command "Get-ChildItem -Path . -Recurse -File -Name '*.pyc' | ForEach-Object { Remove-Item -Path \$$_.FullName -Force -ErrorAction SilentlyContinue }"