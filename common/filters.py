from functools import partial
from typing import Callable, List, Dict

from common.entities import OveMeta


def build_meta_filter(params: Dict) -> Callable:
    include_empty = params.get("includeEmpty", False)
    tag = params.get("filterByTag", None)

    filters = []
    if include_empty:
        filters.append(partial(_include_empty, include_empty=include_empty))

    if tag is not None:
        filters.append(partial(_by_tag, tag=tag))

    return partial(_meta_filter, filters=filters) if len(filters) > 0 else DEFAULT_FILTER


def _meta_filter(meta: OveMeta, filters: List = None) -> bool:
    return all([_filter(meta) for _filter in filters]) if filters is not None else True


def _include_empty(meta: OveMeta, include_empty: bool) -> bool:
    return True if include_empty else meta is not None


# beware: meta can be None
def _by_tag(meta: OveMeta, tag: str) -> bool:
    if tag is None:
        return True
    if meta is None:
        return False
    return tag in meta.tags


DEFAULT_FILTER = partial(_include_empty, include_empty=False)
