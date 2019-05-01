from functools import wraps

from console import Cmd, Choice
from commands.chrome_remote import ChromeRemote

import abc

class Executor(object):
    """Command interface"""

    @classmethod
    def fit(cls, command):
        """ Returns True if the executor can
        execute this command, else False.
        """
        if hasattr(cls, 'regex'):
            return bool(cls.regex.search(command))
        return False

    @abc.abstractmethod
    def execute(self, *args):
        """Execute command"""
        pass


class JSExecutor(Executor):
    """Executor implementation. Executes javascript"""

    def __init__(self, chrome_client):
        self._chrome_client = chrome_client

    def execute(self, command):
        return self._chrome_client.session.evaluate(expression=command)


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
        self.default_executor = list(set(executors) - self.by_regex)[0]

    @pretty_output()
    def execute(self, command):
        return next((e for e in self.by_regex if e.fit(command)),
                        self.default_executor).execute(command)


if __name__ == '__main__':
    chrome_client = ChromeRemote()
    tabs = chrome_client.get_tabs()

    answers = ["{} - {}".format(x['title'].encode('utf-8'), x['url'][0:15]) for x in tabs]
    choice = Choice(title="Choose target tab:", answers=answers).ask()

    target_id = tabs[choice[0]]['id']
    __import__('ipdb').set_trace()
    chrome_client.choose_tab(target_id=target_id)

    command_factory = ExecutorFactory(chrome_client=chrome_client)
    for command in Cmd().cmd_generator():
        command_factory.execute(command)
