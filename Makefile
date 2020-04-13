export GEEKDOC_VERSION ?= latest
BASE_DIR := docs
THEME := hugo-geekdoc
THEME_DIR := $(BASE_DIR)/themes

.PHONY: all
all: doc

.PHONY: doc
doc: doc-assets doc-generate

.PHONY: doc-assets
doc-assets:
  mkdir -p $(THEME_DIR)/$(THEME)/; \
  curl -sSL https://github.com/xoxys/$(THEME)/releases/$${GEEKDOC_VERSION}/download/$(THEME).tar.gz | tar -xz -C $(THEME_DIR)/$(THEME)/ --strip-components=1

.PHONY: doc-generate
doc-generate:
  cd $(BASE_DIR); \
  cp templates/usage_index.md content/usage/_index.md; \
  pydocmd simple corenetworks+ corenetworks.authenticators++ corenetworks.client++ corenetworks.exceptions++ >> content/usage/_index.md

.PHONY: clean
clean:
  rm -rf $(THEME_DIR) && \
  rm -f content/usage/_index.md
