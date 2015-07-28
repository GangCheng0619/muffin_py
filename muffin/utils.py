import asyncio
import hashlib
import hmac
import random
import threading


SALT_CHARS = 'bcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


class MuffinException(Exception):

    """ Implement a Muffin's exception. """

    pass


def abcoroutine(func):
    """ Mark function/method as coroutine.

    Used with Meta classes.

    """
    func._abcoroutine = True
    return func


def to_coroutine(func):
    """ Ensure that the function is coroutine.

    If not convert to coroutine.

    """
    if not asyncio.iscoroutinefunction(func):
        func = asyncio.coroutine(func)
    return func


def create_signature(secret, value, digestmod='sha1', encoding='utf-8'):
    """ Create HMAC Signature from secret for value. """
    if isinstance(secret, str):
        secret = secret.encode(encoding)

    if isinstance(value, str):
        value = value.encode(encoding)

    if isinstance(digestmod, str):
        digestmod = getattr(hashlib, digestmod, hashlib.sha1)

    hm = hmac.new(secret, digestmod=hashlib.sha1)
    hm.update(value)
    return hm.hexdigest()


def check_signature(signature, *args, **kwargs):
    """ Check for the signature is correct. """
    return hmac.compare_digest(signature, create_signature(*args, **kwargs))


def generate_password_hash(password, digestmod='sha1', salt_length=8):
    """ Hash a password with given method and salt length. """

    salt = ''.join(random.sample(SALT_CHARS, salt_length))
    signature = create_signature(salt, password, digestmod=digestmod)
    return '$'.join((digestmod, salt, signature))


def check_password_hash(password, pwhash):
    if pwhash.count('$') < 2:
        return False
    digestmod, salt, signature = pwhash.split('$', 2)
    return check_signature(signature, salt, password, digestmod=digestmod)


class Struct(dict):

    """ `Attribute` dictionary. Use attributes as keys. """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("Attribute '%s' doesn't exists. " % name)

    def __setattr__(self, name, value):
        self[name] = value


class LStruct(Struct):

    """ Locked structure. Used as application/plugins settings.

    Going to be immutable after application is started.

    """

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, '_lock', False)
        super(LStruct, self).__init__(*args, **kwargs)

    def lock(self):
        object.__setattr__(self, '_lock', True)

    def __setitem__(self, name, value):
        if self._lock:
            raise RuntimeError('`%s` is locked.' % type(self))
        super(LStruct, self).__setitem__(name, value)


class local_storage:
    pass


class local:

    """ coroutine.local storage is simular to python's threading.local.

    Usage: ::

        local = muffin.local(loop)
        local.value = 42

    """

    __slots__ = '_loop',
    __loops__ = {}

    def __new__(cls, loop=None):
        """ The local is singleton per loop. """
        key = id(loop)
        if key not in cls.__loops__:
            cls.__loops__[key] = object.__new__(cls)
        return cls.__loops__[key]

    def __init__(self, loop=None):
        """ Bind loop to self. """
        object.__setattr__(self, '_loop', loop or asyncio.get_event_loop())

    def __getattribute__(self, name):
        """ Get attribute from current task's space. """
        if name in ('__setattr__', '__getattr__', '__delattr__', '_loop', '__curtask__'):
            return object.__getattribute__(self, name)
        return getattr(self.__curtask__, name)

    def __setattr__(self, name, value):
        """ Set attribute to current task's space. """
        self.__curtask__.__dict__[name] = value

    def __delattr__(self, name):
        delattr(self.__curtask__, name)

    @property
    def __curtask__(self):
        """ Create namespace in current task. """
        task = asyncio.Task.current_task(loop=self._loop)
        if not task:
            raise RuntimeError('No task is currently running')

        if not hasattr(task, '_locals'):
            task._locals = local_storage()
        return task._locals


tlocals = threading.local()


class slocal(local):

    """ Fail silently to threading.local if curent loop is not running. """

    __loops__ = {}

    def __getattribute__(self, name):
        """ Get attribute from current task's space. """
        if name in ('__setattr__', '__getattr__', '__delattr__', '_loop', '__curtask__'):
            return object.__getattribute__(self, name)

        if self._loop.is_running():
            return getattr(self.__curtask__, name)
        return getattr(tlocals, name)

    def __setattr__(self, name, value):
        """ Set attribute to current task's space. """
        if self._loop.is_running():
            super(slocal, self).__setattr__(name, value)
        else:
            setattr(tlocals, name, value)
