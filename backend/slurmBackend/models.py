"""Models users may select for remote Slurm inference."""

# Add or replace model identifiers in these lists as remote models become available.
SLURM_EMBEDDING_MODELS = [
    "Qwen/Qwen3-Embedding-4B",
]

gecko_models = [
    "Qwen/Qwen3-4B-Instruct-2507", "Qwen/Qwen3-8B"
]

ada_models = [
    "Qwen/Qwen3-4B-Instruct-2507", "Qwen/Qwen3-8B"
]

# Preserve the selectable-model API and order without listing shared models twice.
SLURM_LLM_MODELS = list(dict.fromkeys([*gecko_models, *ada_models]))

# Dedicated fine-tuned Gemma pipeline; not part of the MIL feedback model list.
gemma_partitions = ["wmlg-ada", "gecko"]
