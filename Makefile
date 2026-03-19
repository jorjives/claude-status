VERSION_LOCAL := 0.0.0~local
PKG := claude-status_$(VERSION_LOCAL)_all

.PHONY: test install build clean bump-patch bump-minor bump-major

test:
	PYSTRAY_BACKEND=xorg python3 -m pytest tests/ -v

install:
	./install.sh

build:
	rm -rf "$(PKG)" "$(PKG).deb"
	mkdir -p "$(PKG)/DEBIAN"
	mkdir -p "$(PKG)/usr/share/claude-status"
	mkdir -p "$(PKG)/usr/lib/systemd/user/graphical-session.target.wants"
	sed 's/^Version: VERSION$$/Version: $(VERSION_LOCAL)/' \
		debian/control > "$(PKG)/DEBIAN/control"
	cp debian/postinst "$(PKG)/DEBIAN/postinst"
	cp debian/prerm "$(PKG)/DEBIAN/prerm"
	cp tray.py "$(PKG)/usr/share/claude-status/tray.py"
	cp requirements.txt "$(PKG)/usr/share/claude-status/requirements.txt"
	cp debian/claude-status.service "$(PKG)/usr/lib/systemd/user/claude-status.service"
	ln -s ../claude-status.service \
		"$(PKG)/usr/lib/systemd/user/graphical-session.target.wants/claude-status.service"
	dpkg-deb --root-owner-group --build "$(PKG)"
	@echo "Built $(PKG).deb"

clean:
	rm -rf claude-status_*_all claude-status_*_all.deb

bump-patch bump-minor bump-major:
	@current=$$(git describe --tags --abbrev=0 2>/dev/null || echo v0.0.0); \
	major=$$(echo $$current | sed 's/^v//' | cut -d. -f1); \
	minor=$$(echo $$current | sed 's/^v//' | cut -d. -f2); \
	patch=$$(echo $$current | sed 's/^v//' | cut -d. -f3); \
	case $@ in \
		bump-patch) patch=$$((patch + 1));; \
		bump-minor) minor=$$((minor + 1)); patch=0;; \
		bump-major) major=$$((major + 1)); minor=0; patch=0;; \
	esac; \
	new="v$$major.$$minor.$$patch"; \
	echo "$$current -> $$new"; \
	git tag "$$new" && \
	git push && git push origin "$$new"
