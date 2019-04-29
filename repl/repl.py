from functools import wraps

from console import Cmd
from chrome_remote import ChromeRemote

import abc

class Executor(object):
    """Command interface"""

    @classmethod
    def fit(cls, command):
        if hasattr(cls, 'regex'):
            return cls.regex.search(command)

    @abc.abstractmethod
    def exec(self, *args):
        pass


class JSExecutor(Executor):
    """Execute javascript"""

    def __init__(self, chrome_client):
        self._chrome_client = chrome_client

    def exec(self, command):
        pass


class pretty_output:
    """pretty output"""

    def __call__(self, func):
        @wraps(func)
        def wrapper(this, *args, **kwargs):
            command = kwargs.get('command') or args[0]
            return func(this, command)
        return wrapper


class ExecutorFactory:
    """Command factory"""

    def __init__(self, chrome_client):
        executors = [c(chrome_client) for c in Executor.__subclasses__()]
        self.by_regex = {e for e in executors if hasattr(e, 'regex')}
        # default command is first command without regex
        self.default_executor = (set(executors) - self.by_regex)[0]

    @pretty_output
    def exec(self, command):
        return next((e for e in self.by_regex if e.fit(command)),
                        self.default_executor).exec(command)


if __name__ == '__main__':
    chrome_client = ChromeRemote()
    command_factory = CommandFactory(chrome_client=chrome_client)
    for command in Cmd().cmd_generator():
        chrome_factory.execute(command)
