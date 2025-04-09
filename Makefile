ifeq ($(OS),Windows_NT)
	platform := windows
	executable := zagruz.exe
else
	platform := linux
	executable := zagruz
endif

default: init run

init:
	uv sync --all-extras

run:
	uv run zagruz

build:
	uv build

test:
	uv run python -m unittest discover -s tests -v

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

package:
	uv run pyinstaller \
		--noconfirm \
		--distpath dist/$(platform) \
		package/$(platform).spec

run-package:
	./dist/$(platform)/$(executable)

clean-build:
	rm -rf build/ dist/

clean-venv:
	rm -rf .venv/

clean: clean-build clean-venv

ui-widgets:
	uv run python -m qdarktheme.widget_gallery

ui-themes:
	uv run python -c 'from PyQt6.QtWidgets import QStyleFactory; print(QStyleFactory.keys())'

.PHONY: default init run build test ci-deps-linux package clean-build clean-venv clean widgets
