# Default Model Configuration
# R-ASA components mapped to specific models for optimal performance.

MODEL_CONFIG = {
    # Agents
    "synthesizer": "gemini-2.0-flash", # Strong Reasoning + Coding
    "integrity": "gemini-2.0-flash", # Fast Critic
    "grounding": "ollama/deepseek-r1:8b",   # Use local model to avoid rate limits
    # Domain Specific Models
    "openbiollm": "openrouter/meta-llama/llama-3.1-8b-instruct", # OpenRouter fallback
    "medgemma": "openrouter/google/gemma-2-9b-it", # Medical model via OpenRouter
    "biomistral": "openrouter/mistralai/mistral-7b-instruct", # Alternative biomedical model
    # Default
    "default": "gemini-2.0-flash",
    "ollama": "ollama/deepseek-r1:8b",
    # OpenRouter alternatives
    "openrouter_fallback": "openrouter/anthropic/claude-3-haiku"
}
