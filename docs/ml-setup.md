# ML Service Setup

## Overview

This project uses a separate ML service for real-time strain prediction.

Flow:

1. Frontend tracker batches learner interaction events.
2. Backend `/api/v1/events` stores raw events.
3. Backend aggregates event features and calls ML `/ml/predict`.
4. ML service returns:
   - `strain_level`
   - `confidence`
   - `top_features`
   - `trigger_adaptation`
5. Backend `/adapt` calls GPT-4o-mini to rewrite content.
6. Adapted explanation is returned to the frontend overlay.

---

## ML Service Local Run

From inside `ml/`:

```bash
source .venv/bin/activate
PYTHONPATH=. python -m serve.app