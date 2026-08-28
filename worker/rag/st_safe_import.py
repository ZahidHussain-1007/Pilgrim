"""Load SentenceTransformer without HuggingFace datasets / pyarrow.dataset.

Windows Application Control can block pyarrow's _dataset DLL.
Chat only needs model.encode(). Import this BEFORE sentence_transformers.
"""

from __future__ import annotations

import importlib.machinery
import sys
import types


def _install_stub(name: str) -> types.ModuleType:
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__spec__", None) is not None:
        return existing
    mod = types.ModuleType(name)
    spec = importlib.machinery.ModuleSpec(name, loader=None)
    spec.origin = "pilgrimai-stub"
    spec.submodule_search_locations = []
    mod.__spec__ = spec
    mod.__file__ = "<pilgrimai-stub>"
    mod.__package__ = name
    sys.modules[name] = mod
    return mod


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return _Dummy()


_datasets = _install_stub("datasets")
_datasets.Dataset = _Dummy
_datasets.DatasetDict = _Dummy
_datasets.IterableDataset = _Dummy
_datasets.IterableDatasetDict = _Dummy
_datasets.Value = _Dummy
_datasets.Column = _Dummy
_datasets.__version__ = "0.0.0-stub"

_install_stub("pyarrow.dataset")

from sentence_transformers import SentenceTransformer  # noqa: E402

__all__ = ["SentenceTransformer"]
