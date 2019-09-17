PYTHON = python

HGPATH =
ifneq ($(HGPATH),)
export PYTHONPATH := $(realpath $(HGPATH)):$(PYTHONPATH)
endif

.PHONY: help
help:
	@echo 'Commonly used make targets:'
	@echo '  local        - build for inplace usage'
	@echo '  tests        - run all tests in the automatic test suite'
	@echo '  app          - create a py2app bundle on Mac OS X'
	@echo '  clean        - remove files created by other targets'
	@echo '                 (except installed files or dist source tarball)'
	@echo '  distclean    - remove all files created by other targets'
	@echo '  update-pot   - extract translatable strings'

.PHONY: local
local:
	$(PYTHON) setup.py \
		build_ui \
		build_py -c -d . \
		build_mo
	HGRCPATH= $(PYTHON) thg version

.PHONY: tests
tests:
	@[ -n "$(HGPATH)" ] || { echo "HGPATH not specified"; false; }
	@[ -d "$(HGPATH)" ] || { echo "HGPATH not found: $(HGPATH)"; false; }
	$(PYTHON) tests/run-tests.py -a '!extensions' --with-doctest
	$(PYTHON) tests/run-tests.py -a extensions=largefiles
	$(PYTHON) tests/run-hgtests.py

.PHONY: app
app: DISTDIR = dist/app
app: SETUPCFG = contrib/setup-py2app.cfg
app: export MACOSX_DEPLOYMENT_TARGET=10.7
app:
	@[ -n "$(HGPATH)" ] || { echo "HGPATH not specified"; false; }
	@[ -d "$(HGPATH)" ] || { echo "HGPATH not found: $(HGPATH)"; false; }
	[ -z "$(SETUPCFG)" ] || cp "$(SETUPCFG)" setup.cfg
	$(MAKE) -C "$(HGPATH)" local
	FORCE_SETUPTOOLS= $(PYTHON) setup.py py2app -d "$(DISTDIR)"

.PHONY: clean
clean:
	$(PYTHON) setup.py clean

.PHONY: distclean
distclean: clean
	$(RM) -R build dist

.PHONY: update-pot
update-pot:
	$(PYTHON) setup.py update_pot

docker-centos6:
	$(MAKE) -C contrib/docker build-thg-rpm PLATFORM=centos6

docker-centos7:
	$(MAKE) -C contrib/docker build-thg-rpm PLATFORM=centos7
