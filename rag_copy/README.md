RAG layout (split by scenario ranges):
- `rag_S001-S020/`: baseline snapshot with batch/LLM runs, constraint extraction, vocab/schema, and outputs for S001–S020. Treat as regression reference.
- `rag_S021-S049/`: workspace for mid/late-block scenarios; copy/update scripts/prompts here when extending coverage.
- `rag_S041-S049/`: workspace for tail scenarios; prefer narrower retrieval and conservative prompts to start.

Guidelines:
- Keep `rag_S001-S020/` immutable; branch changes into the range-specific folders.
- Store outputs/reports inside the matching range folder to avoid mixing baselines with experiments.
