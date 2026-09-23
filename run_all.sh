#!/usr/bin/env bash
# Resume/launch the full experiment run. Safe to re-run: completed trials are skipped.
# Requires `ollama serve` running (ideally with OLLAMA_NUM_PARALLEL=4).
cd "$(dirname "$0")/study"
PYTHONIOENCODING=utf-8 /c/Users/yerud/AppData/Local/Python/bin/python3.14.exe run.py \
  --models qwen3:0.6b qwen3:1.7b qwen3:4b qwen3:8b llama3.1:8b mistral:7b gemma4:latest gemma3:12b qwen3:14b phi4:14b \
  --n 30 --out ../data/trials.jsonl --concurrency 8
