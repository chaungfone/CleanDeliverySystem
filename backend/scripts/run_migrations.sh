#!/usr/bin/env bash
# Helper script to run supabase migrations using DIRECT_URL for direct DB connection
# Usage: ./backend/scripts/run_migrations.sh

set -euo pipefail

if [ -z "${DIRECT_URL:-}" ]; then
  echo "DIRECT_URL not set. Please export DIRECT_URL or provide it in the environment."
  exit 2
fi

export DATABASE_URL="$DIRECT_URL"

echo "Using DATABASE_URL for migrations: ${DATABASE_URL}"

# Run supabase db push (assumes supabase CLI is linked or SUPABASE_PROJECT_ID is set)
supabase db push
