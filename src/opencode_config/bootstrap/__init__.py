"""Componentes do bootstrap multiplataforma."""

from .detect import (
    DependencyDetection,
    DependencySpec,
    DependencyStatus,
    detect_dependencies,
    detect_dependency,
)
from .registry import DEPENDENCY_REGISTRY

__all__ = [
    "DEPENDENCY_REGISTRY",
    "DependencyDetection",
    "DependencySpec",
    "DependencyStatus",
    "detect_dependencies",
    "detect_dependency",
]
