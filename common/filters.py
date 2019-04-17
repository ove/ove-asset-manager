from functools import partial
from typing import Callable, List, Dict, Union

from common.entities import OveAssetMeta, OveProjectMeta


def build_meta_filter(params: Dict, default_filter: Callable = None) -> Callable:
    include_empty = params.get("includeEmpty", False)
    tag = params.get("filterByTag", None)

    filters = []
    if include_empty:
        filters.append(partial(_include_empty, include_empty=include_empty))

    if tag is not None:
        filters.append(partial(_by_tag, tag=tag))

    return partial(_meta_filter, filters=filters) if len(filters) > 0 else default_filter


def _meta_filter(meta: Union[OveAssetMeta, OveProjectMeta], filters: List = None) -> bool:
    return all([_filter(meta) for _filter in filters]) if filters is not None else True


def _include_empty(meta: Union[OveAssetMeta, OveProjectMeta], include_empty: bool) -> bool:
    return True if include_empty else meta is not None


# beware: meta can be None
def _by_tag(meta: Union[OveAssetMeta, OveProjectMeta], tag: str) -> bool:
    if tag is None:
        return True
    if meta is None:
        return False
    return tag in meta.tags


DEFAULT_FILTER = partial(_include_empty, include_empty=False)
