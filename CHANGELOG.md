# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-22

### Added

- Project created from python-service-template: layered package with a `/health` endpoint,
  uv, ruff, mypy strict, pytest with an 80% coverage gate, pre-commit hooks, Dockerfile and CI.
- Release workflow: merging a new version to main tags it and publishes release notes from this file.
- OpenF1 data spike (PW-4): `notebooks/01-openf1-spike.ipynb`, findings in `docs/spike-openf1.md`,
  ADR 3 (OpenF1 is the session data source) and ADR 4 (store lap-level data).
