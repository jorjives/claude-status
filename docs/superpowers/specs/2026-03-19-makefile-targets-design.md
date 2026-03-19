# Makefile Targets

## Goal

Add a Makefile with targets for all common project actions, including semver bumping with automatic tag-and-push.

## Targets

| Target | Action |
|---|---|
| `test` | `PYSTRAY_BACKEND=xorg python3 -m pytest tests/ -v` |
| `install` | `./install.sh` |
| `build` | Build .deb locally with version `0.0.0~local` using same layout as CI |
| `clean` | Remove local build artifacts (`claude-status_*_all/` dir and `.deb` file) |
| `bump-patch` | Increment patch version, tag, push commits + tag |
| `bump-minor` | Increment minor version, tag, push commits + tag |
| `bump-major` | Increment major version, tag, push commits + tag |

All targets are `.PHONY`.

## Semver bump logic

1. Get latest tag: `git describe --tags --abbrev=0 2>/dev/null` or default to `v0.0.0`
2. Strip `v` prefix, split on `.`, increment the relevant component (reset lower components to 0)
3. Create tag `vX.Y.Z`
4. `git push && git push origin vX.Y.Z`

Pure bash arithmetic — no external tools.

## Local .deb build

The `build` target replicates the CI workflow's build step locally:

1. Create package directory `claude-status_0.0.0~local_all/`
2. Populate DEBIAN/ (control with version substituted, postinst, prerm)
3. Populate usr/share/claude-status/ (tray.py, requirements.txt)
4. Populate usr/lib/systemd/user/ (service file + wants symlink)
5. Run `dpkg-deb --root-owner-group --build`

## Changes to existing files

- **`.gitignore`:** Add `claude-status_*_all/` and `claude-status_*_all.deb` for local build artifacts.

## New files

- **`Makefile`**
