# Context Engineering Demo

## Setup

```bash
uv sync
cp .env.example .env
# Edit .env — set LLM_PROVIDER, LLM_MODEL, and the matching API key
```

## Run

```bash
# Small app (7 files, 6 bugs)
uv run python -m src.run_traditional
uv run python -m src.run_context

# Large app (15 files, 11 bugs)
uv run python -m src.run_traditional_large
uv run python -m src.run_context_large

# Benchmark (costs real API credits)
uv run python -m src.benchmark          # small app
uv run python -m src.benchmark_large    # large app

# Manual reset
uv run python -m src.manual_reset        # restore apps/target_app/
uv run python -m src.manual_reset_large  # restore apps/target_app_large/
```

## Layout

```
apps/
├── target_app/               # small buggy codebase
├── target_app_bugged/        # snapshot for reset
├── target_app_large/         # large buggy codebase
└── target_app_large_bugged/  # snapshot for reset
results/                      # benchmark output JSON
llm_logs/                     # per-run LLM request/response logs
```
