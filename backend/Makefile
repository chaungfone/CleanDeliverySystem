# Makefile for backend tasks
.PHONY: migrate test

migrate:
	@echo "Run migrations using DIRECT_URL (export DIRECT_URL before running)"
	if [ -z "$(DIRECT_URL)" ]; then \
		echo "DIRECT_URL not set. Use: make migrate DIRECT_URL=postgresql://..."; exit 2; \
	fi
	env DATABASE_URL=$(DIRECT_URL) supabase db push

test:
	pytest tests -q
