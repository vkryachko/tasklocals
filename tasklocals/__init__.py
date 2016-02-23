"Based on python's _threading_local"

from contextlib import contextmanager
from weakref import ref
import asyncio

__all__ = ['local', 'NoTaskError']

_default_local_dct = dict()


class NoTaskError(RuntimeError):
    pass


class _localimpl:
    """A class managing task-local dicts"""
    __slots__ = 'key', 'dicts', 'localargs', '__weakref__', '_loop'

    def __init__(self, loop):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        # The key used in the Thread objects' attribute dicts.
        # We keep it a string for speed but make it unlikely to clash with
        # a "real" attribute.
        self.key = '_task_local._localimpl.' + str(id(self))
        # { id(Task) -> (ref(Task), task-local dict) }
        self.dicts = {}

    def get_dict(self):
        """Return the dict for the current task. Raises KeyError if none
        defined."""
        task = asyncio.Task.current_task(loop=self._loop)
        if task is None:
            raise NoTaskError("No task is currently running")
        return self.dicts[id(task)][1]

    def create_dict(self):
        """Create a new dict for the current task, and return it."""
        localdict = {}
        key = self.key
        task = asyncio.Task.current_task(loop=self._loop)
        if task is None:
            raise NoTaskError("No task is currently running")
        idt = id(task)
        def local_deleted(_, key=key):
            # When the localimpl is deleted, remove the task attribute.
            task = wrtask()
            if task is not None:
                del task.__dict__[key]
        def task_deleted(_, idt=idt):
            # When the task is deleted, remove the local dict.
            # Note that this is suboptimal if the task object gets
            # caught in a reference loop. We would like to be called
            # as soon as the task ends instead.
            local = wrlocal()
            if local is not None:
                dct = local.dicts.pop(idt)
        wrlocal = ref(self, local_deleted)
        wrtask = ref(task, task_deleted)
        task.__dict__[key] = wrlocal
        self.dicts[idt] = wrtask, localdict
        return localdict


@contextmanager
def _patch(self):
    impl = object.__getattribute__(self, '_local__impl')
    strict = object.__getattribute__(self, '_strict')
    try:
        dct = impl.get_dict()
    except KeyError:
        dct = impl.create_dict()
        args, kw = impl.localargs
        self.__init__(*args, **kw)
    except NoTaskError:
        if strict:
            raise
        dct = _default_local_dct
    object.__setattr__(self, '__dict__', dct)
    yield


class local:
    __slots__ = '_local__impl', '__dict__', '_strict'

    def __new__(cls, *args, loop=None, strict=True, **kw):
        if (args or kw) and (cls.__init__ is object.__init__):
            raise TypeError("Initialization arguments are not supported")
        self = object.__new__(cls)
        impl = _localimpl(loop=loop)
        impl.localargs = (args, kw)
        object.__setattr__(self, '_local__impl', impl)
        object.__setattr__(self, '_strict', strict)
        return self

    def __getattribute__(self, name):
        with _patch(self):
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name == '__dict__':
            raise AttributeError(
                "%r object attribute '__dict__' is read-only"
                % self.__class__.__name__)
        with _patch(self):
            return object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name == '__dict__':
            raise AttributeError(
                "%r object attribute '__dict__' is read-only"
                % self.__class__.__name__)
        with _patch(self):
            return object.__delattr__(self, name)
