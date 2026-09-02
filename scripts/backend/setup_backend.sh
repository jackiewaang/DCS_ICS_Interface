#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/backend"
VENV="$APP_DIR/venv-backend"

# Install backend dependencies
if [[ ! -d "$VENV" ]]; then
    python3.11 -m venv "$VENV"
    "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
fi

# Install SpaCy models for entity extraction
for model in en_core_web_sm en_core_web_trf; do
    if ! "$VENV/bin/python" -c "import spacy.util; raise SystemExit(not spacy.util.is_package('$model'))"; then
        "$VENV/bin/python" -m spacy download "$model"
    fi
done

# Install nltk for sentiment analysis
if ! "$VENV/bin/python" -c 'import nltk; nltk.data.find("sentiment/vader_lexicon.zip")' 2>/dev/null; then
    "$VENV/bin/python" -m nltk.downloader vader_lexicon
fi
