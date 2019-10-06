import threading
try
    import Queue as queue
except ImportError:
    import queue
import os


class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})): pass


class SelectableQueue(queue.Queue):
    def __init__(self):
        super().__init__()
        self._putsocket, self._getsocket = socket.socketpair()

    def fileno(self):
        return self._getsocket.fileno()

    def put(self, item):
        super().put(item)
        self._putsocket.send(b'x')

    def get(self):
        self._getsocket.recv(1)
        return super().get()

    def is_not_empty(self):
        return not super().empty()


print_mutex = threading.Lock()
def locked_print(message):
    print_mutex.acquire()
    print(message)
    print_mutex.release()
