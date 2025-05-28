VERSION := $(shell uv run python -c 'from importlib.metadata import version; print(version("zagruz"))')

ifeq ($(OS),Windows_NT)
	PLATFORM := windows
	EXECUTABLE := zagruz-win-$(VERSION).exe
else
	PLATFORM := linux
	EXECUTABLE := zagruz-linux-$(VERSION)
endif

default: init run

init:
	uv sync --all-extras

wheel:
	uv build --wheel --out-dir ./dist/wheel/

package:
	uv run --with toml ./scripts/generate_version.py
	uv run pyinstaller \
		--noconfirm \
		--distpath dist/$(PLATFORM) \
		package/$(PLATFORM).spec
	rm -f ./src/zagruz/_version.py

run:
	uv run zagruz

run-wheel:
	@# sometimes old version of wheel is taken from cache
	@# to remove it run: make clean-cache
	uvx ./dist/wheel/zagruz-*.whl zagruz

run-package:
	./dist/$(PLATFORM)/$(EXECUTABLE)

test:
	uv run python -m unittest discover -s tests -v

clean-cache:
	uv cache prune

clean-build:
	rm -rf build/ dist/

clean-venv:
	rm -rf .venv/

clean: clean-build clean-venv

# translations

lang: lang-gen lang-comp

lang-gen:
	uv run pyside6-lupdate src/zagruz/*.py -ts src/zagruz/translations/*.ts

lang-comp:
	uv run pyside6-lrelease src/zagruz/translations/*.ts

# utils

version:
	@echo $(VERSION)

ci-deps-linux:
	sudo apt-get update
	sudo apt-get install -y \
	  libxcb-cursor0 \
	  libxcb-keysyms1 \
	  libxcb-render-util0 \
	  libxcb-xkb1 \
	  libxkbcommon-x11-0 \
	  libxcb-icccm4 \
	  libxcb-image0 \
	  libxcb-shape0

ui-widgets:
	uv run python -m qdarktheme.widget_gallery

ui-themes:
	@uv run python -c 'from PySide6.QtWidgets import QStyleFactory; print(QStyleFactory.keys())'

.PHONY: default init wheel package run run-wheel run-package test clean-build clean-cache clean-venv clean lang lang-gen lang-comp ci-deps-linux ui-widgets ui-themes
