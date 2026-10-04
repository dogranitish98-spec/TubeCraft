"""core — lazy public exports.

Historically this package eagerly imported every API/audio/pipeline module at
``import core`` time. That made lightweight utilities, self-tests and diagnostics
fail when an optional media dependency was absent. Public names remain available,
but expensive modules are now imported only when the corresponding name is used.
"""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "AgnesImageAPI": ("core.api", "AgnesImageAPI"),
    "AgnesVideoAPI": ("core.api", "AgnesVideoAPI"),
    "AgnesChatAPI": ("core.api", "AgnesChatAPI"),
    "EdgeTTSEngine": ("core.audio.tts", "EdgeTTSEngine"),
    "SilentTTSEngine": ("core.audio.tts", "SilentTTSEngine"),
    "SubtitleGenerator": ("core.audio", "SubtitleGenerator"),
    "VideoConcatenator": ("core.compositor", "VideoConcatenator"),
    "VideoProcessor": ("core.compositor", "VideoProcessor"),
    "BasePipeline": ("core.pipelines", "BasePipeline"),
    "PipelineShutdown": ("core.pipelines", "PipelineShutdown"),
    "SimpleVideoPipeline": ("core.pipelines", "SimpleVideoPipeline"),
    "CreativeVideoPipeline": ("core.pipelines", "CreativeVideoPipeline"),
    "ManuscriptVideoPipeline": ("core.pipelines", "ManuscriptVideoPipeline"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if not target:
        raise AttributeError(f"module 'core' has no attribute {name!r}")
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
