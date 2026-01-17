install:
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run

build:
	./build.sh

start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	/opt/render/.local/bin/uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app