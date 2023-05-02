all: clean build install
.PHONY: all

clean:
	rm -fv ./t0rr3sp3dr0-nix-*.tar.gz
.PHONY: clean

build:
	ansible-galaxy collection build --force
.PHONY: build

install:
	ansible-galaxy collection install ./t0rr3sp3dr0-nix-*.tar.gz --force
.PHONY: install

publish:
	ansible-galaxy collection publish ./t0rr3sp3dr0-nix-*.tar.gz
.PHONY: publish
