export GEEKDOC_VERSION ?= latest
THEME := hugo-geekdoc
BASEDIR := docs
THEMEDIR := $(BASEDIR)/themes
APIDIR := $(BASEDIR)/content/api
PACKAGE := corenetworks

.PHONY: all
all: doc

.PHONY: doc
doc: doc-assets doc-generate

.PHONY: doc-assets
doc-assets:
	mkdir -p $(THEMEDIR)/$(THEME)/ ; \
	curl -sSL "https://github.com/thegeeklab/$(THEME)/releases/$${GEEKDOC_VERSION}/download/$(THEME).tar.gz" | tar -xz -C $(THEMEDIR)/$(THEME)/ --strip-components=1

.PHONY: doc-generate
doc-generate:
	pdoc --template-dir $(BASEDIR)/templates/ -o $(APIDIR) --force \
		$(PACKAGE).authenticators \
		$(PACKAGE).client \
		$(PACKAGE).exceptions

.PHONY: clean
clean:
	rm -rf $(THEMEDIR) && \
	rm -rf $(APIDIR)/$(PACKAGE)
