#!/bin/bash
set -e

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
APP_DIR="$REPO_ROOT/backend"
VENV="$APP_DIR/venv-backend"

#module load Python/3.11.5-GCCcore-13.2.0 - uncomment to load Python module if not loaded

if [[ ! -d "$VENV" ]]; then
    python3.11 -m venv "$VENV"
    "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
fi

for model in en_core_web_sm en_core_web_trf; do
    if ! "$VENV/bin/python" -c "import spacy.util; raise SystemExit(not spacy.util.is_package('$model'))"; then
        "$VENV/bin/python" -m spacy download "$model"
    fi
done

if ! "$VENV/bin/python" -c 'import nltk; nltk.data.find("sentiment/vader_lexicon.zip")' 2>/dev/null; then
    "$VENV/bin/python" -m nltk.downloader vader_lexicon
fi
