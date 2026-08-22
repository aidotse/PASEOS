# CLAUDE.md

Guidance for Claude Code when working with the PASEOS repository.

## Project Overview

PASEOS (PAseos Simulates the Environment for Operating multiple Spacecraft) is a
decentralised `Python` module that simulates operational and onboard constraints
(power, thermal, radiation, communication windows, orbital dynamics) for one or
many spacecraft. One PASEOS instance runs per node (actor); each instance models
its own local actor and tracks known actors. See the README for a full feature
tour and the paper (arXiv:2302.02659) for background.

## Environment & Commands

PASEOS depends on `pykep`, which drives the toolchain. The code uses the **pykep
2.x API** (`pk.epoch`, `pk.planet.jpl_lp`, ...); pykep 3.x is an incompatible
rewrite and is **not** supported. pykep 2.6 only ships pip wheels up to Python
3.8 (Linux). Two supported setups:

```bash
# conda / mamba (cross-platform, modern Python via conda-forge pykep)
conda env create -f environment.yml
conda activate paseos

# uv (Linux + Python 3.8, pip-installable pykep 2.6)
uv venv --python 3.8
uv pip install -e ".[dev]"
```

```bash
# Run tests
uv run pytest                                   # or: pytest (inside the env)
pytest paseos/tests/actor_builder_test.py -v    # single file
pytest paseos/tests/actor_builder_test.py::test_name -v

# Lint + format (must pass before committing)
ruff check .            # lint
ruff check --fix .      # lint and auto-fix
ruff format .           # format
ruff format --check .   # verify formatting
```

## Coding Instructions

1. Follow PEP 8; keep production code ready-to-run.
2. Use pytest for unit and integration tests. Tests live in `paseos/tests/` and
   are named `*_test.py`.
3. **Fail hard, no fallbacks:** prefer direct `dict["key"]` and direct config
   access over `.get()` / `getattr()` with defaults. Let errors propagate.
4. **Docstrings:** Google style (`Args`, `Returns`, `Raises`). Comments explain
   *why*, not *what*.
5. **Commit messages** MUST follow Conventional Commits: `<type>(<scope>): <desc>`
   (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`,
   `build`). Never mention Claude, Claude Code, Anthropic, or AI assistance.

**IMPORTANT:** Run the test suite after changes and make sure it passes.

## Architecture

Package root: `paseos/`. Public API is re-exported from `paseos/__init__.py`.

| Component        | Location                              | Purpose                                                        |
| ---------------- | ------------------------------------- | -------------------------------------------------------------- |
| PASEOS instance  | `paseos/paseos.py`                    | Simulation loop, time advancement, activity orchestration      |
| ActorBuilder     | `paseos/actors/actor_builder.py`      | Modular construction of actors (orbit, power, thermal, ...)    |
| Actors           | `paseos/actors/`                      | `BaseActor`, `SpacecraftActor`, `GroundstationActor`           |
| Central body     | `paseos/central_body/`                | Central body, eclipse and line-of-sight geometry               |
| Activities       | `paseos/activities/`                  | Async activity registration and execution                      |
| Physical models  | `paseos/power/`, `paseos/thermal/`, `paseos/radiation/` | Power/battery, thermal, radiation models     |
| Communication    | `paseos/communication/`               | Communication windows, line-of-sight passes                    |
| Attitude         | `paseos/attitude/`                    | Attitude modelling                                             |
| Geometric model  | `paseos/geometric_model/`             | Mesh-based geometry for custom central bodies                  |
| Visualization    | `paseos/visualization/`               | Interactive and animated plotting                              |
| Utils / cfg      | `paseos/utils/`, `paseos/resources/`  | Config loading/validation, default cfg, ephemeris data         |

### Key Design Patterns

- **Decentralised:** one instance per actor; the local actor is fully simulated,
  known actors are tracked.
- **Config via DotMap:** load defaults with `load_default_cfg()`
  (`paseos/utils/load_default_cfg.py`), validate in `check_cfg.py`; defaults live
  in `paseos/resources/default_cfg.toml`.
- **Modular actors:** build actors with `ActorBuilder` rather than constructors.
- **Extensible:** custom propagators, custom central bodies (meshes), and custom
  properties let users wrap external software (see README).

## Documentation Maintenance

Update this file when architecture, components, commands, or the supported
Python/pykep setup change. Use the `#` key during a session to jot quick notes.
