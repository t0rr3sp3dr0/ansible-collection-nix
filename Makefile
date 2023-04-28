all:
.PHONY: all

build: 
	ansible-galaxy collection build --force
.PHONY: build

publish:
	ansible-galaxy collection publish ./t0rr3sp3dr0-nix-*.tar.gz
.PHONY: publish
