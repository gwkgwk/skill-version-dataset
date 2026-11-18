---
name: "add-model"
display_name: "Add New Model Definition"
description: "Add a new ModelDefinition singleton under src/elements/models/ for use in agent definitions."
version: "2.0"
triggers:
  - "Prompt contains: 'add model', 'new model', 'register model', 'add model definition'"
  - "User references a model ID not yet present in elements/models/"
permissions: ["read:src", "write:src"]
---

# Purpose

Create a `ModelDefinition` singleton under `src/elements/models/<provider>/`. Model definitions are the **single authoritative location** for model IDs and provider settings in the codebase. Never hard-code a model ID string outside `elements/models/`.

---

# Step 1 — Identify provider and model ID

**Supported providers** (`ModelProviderType` in `src/core/agent_base/definitions/constants.py`):

| Enum value | String | Usage |
|---|---|---|
| `ModelProviderType.OPENAI` | `"openai"` | OpenAI API (gpt-5, gpt-4o, gpt-4o-mini …) |
| `ModelProviderType.ANTHROPIC` | `"anthropic"` | Anthropic API (claude-opus-4-5, claude-sonnet-4-6 …) |
| `ModelProviderType.OLLAMA` | `"ollama"` | Local Ollama server (llama3, mistral, codellama …) |
| `ModelProviderType.GROQ` | `"groq"` | Groq API (llama-3.1-70b-versatile …) |

Confirm:
- **Provider string** (one of the four above)
- **Exact `model_id`** matching the provider's API identifier
- **Optional config:** `temperature` (0.0–2.0), `max_tokens` (positive int), `top_p` (0.0–1.0)
- **Optional `api_key`:** use `$ENV_VAR` syntax for non-default keys
- **Optional `base_url`:** required for Ollama; optional for Azure OpenAI or custom endpoints

---

# Step 2 — Determine file location

| Provider | Directory |
|---|---|
| OpenAI | `src/elements/models/openai/` |
| Anthropic | `src/elements/models/anthropic/` |
| Ollama | `src/elements/models/ollama/` |
| Groq | `src/elements/models/groq/` |

Name the file after the model family (e.g. `gpt_4o.py`, `claude_sonnet.py`, `llama3.py`). Multiple variants can co-exist in the same file as separate singletons.

---

# Step 3 — Create the model file

```python
from core.agent_base.definitions.model_definition import ModelDefinition

# Minimal
<model_slug>_model_def = ModelDefinition(
    provider="<provider>",        # "openai" | "anthropic" | "ollama" | "groq"
    model_id="<exact-model-id>",
)

# With sampling config
<model_slug>_tuned_model_def = ModelDefinition(
    provider="<provider>",
    model_id="<exact-model-id>",
    config={
        "temperature": 0.0,   # float 0.0–2.0 (validated)
        "max_tokens": 4096,   # positive int (validated)
        "top_p": 0.95,        # float 0.0–1.0 (validated)
    }
)

# Explicit API key from environment variable
<model_slug>_keyed_model_def = ModelDefinition(
    provider="<provider>",
    model_id="<exact-model-id>",
    api_key="$MY_API_KEY_VAR",   # resolved from os.environ at agent build time
)

# Ollama local server
llama3_model_def = ModelDefinition(
    provider="ollama",
    model_id="llama3",
    base_url="http://localhost:11434",
)
```

**`ModelDefinition` validation rules:**
- `provider`: case-insensitive; must be `"openai"`, `"anthropic"`, `"ollama"`, or `"groq"`
- `model_id`: non-empty; not validated against the provider API — use the exact identifier from provider docs
- `config.temperature`: `float` in `[0.0, 2.0]`
- `config.max_tokens`: positive `int`
- `config.top_p`: `float` in `[0.0, 1.0]`
- `api_key`: `$ENV_VAR` strings resolved from `os.environ` at agent build time
- `ModelDefinition` is `frozen=True` — immutable after construction

---

# Step 4 — Create `README.md` (if new provider directory)

If creating the first model in a new provider directory, create a `README.md` using the canonical 7-section template (see `documentation-update` Skill).

---

# Examples

**OpenAI GPT-4o:**
```python
# src/elements/models/openai/gpt_4o.py
from core.agent_base.definitions.model_definition import ModelDefinition

gpt_4o_model_def = ModelDefinition(provider="openai", model_id="gpt-4o")
gpt_4o_mini_model_def = ModelDefinition(
    provider="openai", model_id="gpt-4o-mini",
    config={"temperature": 0.0, "max_tokens": 2048}
)
```

**Anthropic Claude:**
```python
# src/elements/models/anthropic/claude_sonnet.py
from core.agent_base.definitions.model_definition import ModelDefinition

claude_sonnet_model_def = ModelDefinition(
    provider="anthropic", model_id="claude-sonnet-4-6",
    api_key="$ANTHROPIC_API_KEY"
)
```

**Ollama local:**
```python
# src/elements/models/ollama/llama3.py
from core.agent_base.definitions.model_definition import ModelDefinition

llama3_model_def = ModelDefinition(
    provider="ollama", model_id="llama3",
    base_url="http://localhost:11434"
)
```

---

# Failure Modes

| Situation | Action |
|---|---|
| Provider not in `ModelProviderType` | Do not create the file. The provider must first be added to the enum and have a framework adapter. |
| `model_id` not confirmed | Create with `# TODO: verify model_id with provider docs` comment. |
| `config` value out of range | `ModelDefinition` validator raises at instantiation. Report valid range to user. |
