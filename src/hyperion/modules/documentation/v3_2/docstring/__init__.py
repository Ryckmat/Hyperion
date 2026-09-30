"""Génération de docstrings v3.2."""

from .generator import DocstringGenerator
from .styles import GOOGLE_STYLE, NUMPY_STYLE, SPHINX_STYLE, STYLES, DocstringTemplate

__all__ = [
    "DocstringGenerator",
    "STYLES",
    "DocstringTemplate",
    "GOOGLE_STYLE",
    "NUMPY_STYLE",
    "SPHINX_STYLE",
]
