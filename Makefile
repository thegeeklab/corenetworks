# renovate: datasource=github-releases depName=thegeeklab/hugo-geekdoc
THEME_VERSION := v0.10.0
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
	curl -sSL "https://github.com/thegeeklab/$(THEME)/releases/download/${THEME_VERSION}/$(THEME).tar.gz" | tar -xz -C $(THEMEDIR)/$(THEME)/ --strip-components=1
.PHONY: doc-generate
doc-generate:
	poetry run pdoc --template-dir $(BASEDIR)/templates/ -o $(APIDIR) --force \
		$(PACKAGE).authenticators \
		$(PACKAGE).client \
		$(PACKAGE).exceptions

.PHONY: clean
clean:
	rm -rf $(THEMEDIR) && \
	rm -rf $(APIDIR)/$(PACKAGE)
