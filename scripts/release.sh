#!/bin/sh

version="$(uv version --short --bump patch)"
git add pyproject.toml uv.lock
git commit -m "release: v$version"
git tag "v$version"
git push origin "v$version"
