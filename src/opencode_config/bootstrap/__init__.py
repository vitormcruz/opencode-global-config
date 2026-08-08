"""Componentes do bootstrap multiplataforma."""

from .detect import (
    DependencyDetection,
    DependencySpec,
    DependencyStatus,
    detect_dependencies,
    detect_dependency,
)
from .interactive import (
    BootstrapResult,
    InteractiveError,
    render_detection_table,
    run_bootstrap,
)
from .registry import DEPENDENCY_REGISTRY

__all__ = [
    "DEPENDENCY_REGISTRY",
    "DependencyDetection",
    "DependencySpec",
    "DependencyStatus",
    "BootstrapResult",
    "InteractiveError",
    "detect_dependencies",
    "detect_dependency",
    "render_detection_table",
    "run_bootstrap",
]
