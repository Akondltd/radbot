"""
RadBot Security Module

Provides supply chain attack protection for Python dependencies.
"""
from .startup_check import DependencyVerifier

__all__ = ['DependencyVerifier']
