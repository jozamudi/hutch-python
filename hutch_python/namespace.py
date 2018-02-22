from inspect import isfunction
import logging

from .utils import (IterableNamespace, find_class, strip_prefix,
                    get_all_objects)

logger = logging.getLogger(__name__)


def class_namespace(cls, scope=None):
    """
    Create a namespace that contains objects of a specific type.

    Parameters
    ----------
    cls: type or str

    scope: module, namespace, or list of these
        Every object attached to the given modules will be considered for the
        class_namespace. If scope is omitted, we'll check all objects loaded by
        hutch_python and everything in the caller's global frame.

    Returns
    -------
    namespace: IterableNamespace
    """
    logger.debug('Create class_namespace cls=%s, scope=%s', cls, scope)
    class_space = IterableNamespace()
    scope_objs = get_all_objects(scope=scope, stack_offset=1)

    if isinstance(cls, str):
        if cls != 'function':
            try:
                cls = find_class(cls)
            except Exception as exc:
                err = 'Type {} could not be loaded'
                logger.error(err.format(cls))
                logger.debug(exc, exc_info=True)
                return class_space

    for name, obj in scope_objs.items():
        if cls == 'function':
            if isfunction(obj):
                setattr(class_space, name, obj)
        elif isinstance(obj, cls):
            setattr(class_space, name, obj)

    return class_space


def metadata_namespace(md, scope=None):
    """
    Create a namespace that accumulates objects and creates a tree based on
    their metadata.

    Parameters
    ----------
    md: list of str
        Each of the metadata categories to group objects by, in order from the
        root of the tree to the leaves.

    scope: module, namespace, or list of these
        Every object attached to the given modules will be considered for the
        metadata_namespace. If scope is omitted, we'll check all objects loaded
        by hutch_python and everything in the caller's global frame.

    Returns
    -------
    namespace: IterableNamespace
    """
    logger.debug('Create metadata_namespace md=%s, scope=%s', md, scope)
    metadata_space = IterableNamespace()
    scope_objs = get_all_objects(scope=scope, stack_offset=1)

    for name, obj in scope_objs.items():
        # Collect obj metadata
        if hasattr(obj, 'md'):
            raw_keys = [getattr(obj.md, filt, None) for filt in md]
        # Fallback: try using_the_name
        else:
            name_keys = name.split('_')
            raw_keys = [None] * len(md)
            for i, key in enumerate(name_keys):
                if i >= len(md):
                    break
                if key == md[i]:
                    raw_keys[i] = key
                else:
                    break
        # Abandon if no matches
        if raw_keys[0] is None:
            continue
        # Force lowercase
        keys = []
        for key in raw_keys:
            if isinstance(key, str):
                keys.append(key.lower())
            else:
                keys.append(key)
        # Add key to existing namespace branch, create new if needed
        logger.debug('Add %s to namespace metadata', name)
        upper_space = metadata_space
        for key in keys:
            if key is None:
                break
            name = strip_prefix(name, key)
            if not hasattr(upper_space, key):
                setattr(upper_space, key, IterableNamespace())
            upper_space = getattr(upper_space, key)
        setattr(upper_space, name, obj)
    return metadata_space
