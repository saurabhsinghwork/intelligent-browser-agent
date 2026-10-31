"""Compatibility imports for the historically misnamed Grok module.

New application code uses GroqProvider. These aliases preserve existing imports
without preserving the incorrect provider label or the text-only model selection.
"""
# Import the correctly named Groq Qwen implementation.
from models.groq_provider import GroqProvider, GROQ_MODEL
# Keep older class imports functional while application code migrates to Groq.
GrokProvider = GroqProvider
# Preserve the legacy constant without retaining its previous model value.
GROK_MODEL = GROQ_MODEL
