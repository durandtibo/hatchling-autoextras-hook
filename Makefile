SHELL = /bin/bash

include .make/all.mk

.PHONY: all
all: format lint test ## Format, lint and test the project

.PHONY: test
test: ## Run the tests
	.venv/bin/pytest tests

.PHONY: clean
clean: ## Remove build, test and cache artifacts
	.venv/bin/inv clean.all
