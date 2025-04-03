ifeq ($(OS),Windows_NT)
	platform := windows
else
	platform := linux
endif

init:
	uv sync --all-extras

build:
	uv build

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

clean:
	rm -rf build/ dist/

.PHONY: init ci-deps-linux package
