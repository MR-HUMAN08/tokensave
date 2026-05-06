    # Paisa changes summary (since your critical bug-fix request)

    ## Files updated
    - paisa/router.py
    - Switched Google model to gemini/gemini-1.5-flash.
    - Added provider-aware routing with key filtering and priority.
    - Added token efficiency and quality scoring for label-based selection.
    - Added get_best_model_for_keys() and get_preferred_model_for_label().
    - Added helper for provider lookup from model.

    - paisa/fallback.py
    - Added provider env var mapping and per-attempt env injection.
    - Fallback now tries available providers for the same label.
    - Added model-to-provider and model-to-label helpers.

    - paisa/cli.py
    - Suppressed LiteLLM logs via LITELLM_LOG + logging level.
    - Shows scenario after keys list (single vs multi provider).
    - Prints classification and routing decision before call.
    - Passes keys to router and fallback; updates provider used if fallback occurs.

    - paisa/classifier.py
    - Replaced heuristic classifier with local sentence-transformer based classifier.
    - Outputs SIMPLE/MODERATE/COMPLEX with confidence score.

    - setup.py / pyproject.toml / paisa/__init__.py
    - Bumped version to 0.1.5.
    - Added sentence-transformers and torch to dependencies for classifier.

    - requirements.txt
    - Added sentence-transformers and torch.

    ## Build output
    - Rebuilt dist artifacts for 0.1.5:
    - dist/paisa-0.1.5.tar.gz
    - dist/paisa-0.1.5-py3-none-any.whl

    ## Notes
    - Routing now only uses providers with stored keys.
    - Fallback attempts only providers with keys and for the same label.
    - Gemini model name fixed to gemini/gemini-1.5-flash.
