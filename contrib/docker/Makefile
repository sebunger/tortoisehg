DOCKER = docker

PLATFORM =
CONTAINER = thgrun/$(PLATFORM)

RUNGID = $(shell id -g)
RUNGROUP = $(shell id -gn)
RUNUID = $(shell id -u)
RUNUSER = $(shell id -un)
RUNDISPLAY = unix$(DISPLAY)
RUNHOME = $(HOME)
RUNSHELL = /bin/bash
RUNWORKDIR = $(CURDIR)/../..
REPOROOT = $(shell hg root)
DOCKERREPO = /thgrepo/
HGRPM = /mercurial.rpm

help:
	@echo 'Make targets:'
	@echo '  build         - build new image for the specified platform'
	@echo '  shell         - run $(RUNSHELL) in new container'
	@echo '  build-thg-rpm - build thg rpm for the specified platform'
	@echo
	@echo 'Example to start shell in CentOS 6 container:'
	@echo '  make shell DOCKER="sudo docker" PLATFORM=centos6'

build: $(PLATFORM)
	@[ -n "$<" ] || { echo 'PLATFORM must be specified' >&2; false; }
	{ \
		cat $<; \
		echo RUN groupadd $(RUNGROUP) -g $(RUNGID); \
		echo RUN useradd $(RUNUSER) -u $(RUNUID) -g $(RUNGID) \
			-d $(RUNHOME) -s $(RUNSHELL); \
	} | $(DOCKER) build --build-arg http_proxy --build-arg https_proxy \
		--tag $(CONTAINER) -

shell: build
	$(DOCKER) run -e http_proxy -e https_proxy -u $(RUNUSER) -it --rm \
		-e DISPLAY=$(RUNDISPLAY) \
		-v /tmp:/tmp -v $(RUNHOME):$(RUNHOME) -w $(RUNWORKDIR) \
		$(CONTAINER) $(RUNSHELL) -l

build-thg-rpm: build
	$(DOCKER) run -e http_proxy -e https_proxy -u $(RUNUID):$(RUNGID) --rm \
		-v $(REPOROOT):$(DOCKERREPO) \
		-w $(DOCKERREPO) \
		-v $(shell readlink -f ./mercurial.rpm):$(HGRPM) \
		$(CONTAINER) ./contrib/rpm.sh \
		--rpmbuilddir rpmbuild/$(PLATFORM) --installhg $(HGRPM)

.PHONY: help build shell
