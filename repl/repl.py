from functools import wraps

from console import Choice, locked_print
from commands.chrome_remote import ChromeRemote

from termcolor import colored

import abc, sys, json, re

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JavascriptLexer

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


class ExecutorFactory:
    """Command factory"""

    def __init__(self, chrome_client):
        executors = [c(chrome_client) for c in Executor.__subclasses__()]
        self.by_regex = {e for e in executors if hasattr(e, 'regex')}
        # default command is first command without regex
        self.default_executor = list(set(executors) - self.by_regex)[0]

    def execute(self, command):
        return next((e for e in self.by_regex if e.fit(command)),
                        self.default_executor).execute(command)


class DefaultOutputHandler(object):
    def __init__(self):
        pass

    def process(self, result):
        value = result.get('description', None) or result.get('value', None)
        return {
            'class_name': None,
            'value': value
        }


class BooleanOutputHandler(object):

    def __init__(self, factory, chrome_client):
        self.chrome_client = chrome_client
        self.factory = factory

    def process(self, result):
        value = result['value']
        return {
            'class_name': None,
            'value': 'true' if value else 'false'
        }


class ObjectOutputHandler(object):

    def __init__(self, factory, chrome_client):
        self.chrome_client = chrome_client
        self.factory = factory

    def process_object(self, result):
        class_name = result['className']
        description = result['description']
        object_id = result['objectId']
        properties = self.chrome_client.session.send("Runtime.getProperties",
            objectId=object_id, ownProperties=True)['result']

        reject_proto = lambda prop : prop['name'] != '__proto__'
        properties = filter(reject_proto, properties)

        _object = {}
        for prop in properties:
            _object[prop['name']] = prop['value'].get('value', prop['value']['type'])
        value = json.dumps(_object)
        value = re.sub(r'\"(\w+)\": ', r'\1: ', value)
        value = re.sub(r'\"(function)\"', 'function', value)
        value = re.sub(r'\"(object)\"', '{...}', value)
        return {
            'class_name': class_name,
            'value': value
        }

    def process_error(self, result):
        class_name = result['className']
        value = result['description']
        return {
            'class_name': class_name,
            'value': value
        }

    def process(self, result):
        __import__('ipdb').set_trace()
        subtype = result.get('subtype', None)
        if subtype and subtype == 'error':
            return self.process_error(result)
        else:
            return self.process_object(result)




class FunctionOutputHandler(object):

    def __init__(self, factory, chrome_client):
        self.chrome_client = chrome_client
        self.factory = factory

    def process(self, result):
        class_name = result['className']
        script_source = result['description']
        return {
            'class_name': class_name,
            'value': script_source
        }


class UndefinedOutputHandler(object):

    def __init__(self, factory, chrome_client):
        self.chrome_client = chrome_client
        self.factory = factory

    def process(self, result):
        return {
            'class_name': None,
            'value': 'undefined'
        }


class StringOutputHandler(object):

    def __init__(self, factory, chrome_client):
        self.chrome_client = chrome_client
        self.factory = factory

    def process(self, result):
        return {
            'class_name': None,
            'value': "\"{}\"".format(result['value'])
        }


class OutputHandlerFactory(object):

    def __init__(self, chrome_client):
        self.handlers = {}
        self.handlers['object'] = ObjectOutputHandler(self, chrome_client)
        self.handlers['function'] = FunctionOutputHandler(self, chrome_client)
        self.handlers['undefined'] = UndefinedOutputHandler(self, chrome_client)
        self.handlers['string'] = StringOutputHandler(self, chrome_client)
        self.handlers['boolean'] = BooleanOutputHandler(self, chrome_client)
        self.handlers['default'] = DefaultOutputHandler()

    def process(self, result={}):
        _type = result.get('type', 'default')
        handler = self.handlers.get(_type, self.handlers['default'])
        return handler.process(result)


def console_log(**event):
    """Pretty print console messages.

    :event: Console.messageAdded event
    :returns: None

    """
    message = event.get('message', None)

    if not message:
        return None
    elif message['level'] == 'log':
        locked_print(message['text'])
    elif message['level'] == 'warning':
        text = colored(message['text'], 'yellow')
        locked_print(text)
    elif message['level'] == 'error':
        text = colored(message['text'], 'red')
        locked_print(text)
    elif message['level'] == 'debug':
        text = colored(message['text'], 'grey')
        locked_print(text)
    elif message['level'] == 'info':
        text = colored(message['text'], 'blue')
        locked_print(text)


lexer = JavascriptLexer()
formatter = TerminalFormatter()

def pretty_print(class_name=None, value=None):
    class_name = colored("[ {} ]".format(class_name), 'yellow') if class_name else None
    if type(value) == dict:
        value = json.dumps(value)
    value = highlight(str(value), lexer, formatter)[:-1]
    output = filter(lambda out: out != None, [class_name, value])
    locked_print(" ".join(output))


if __name__ == '__main__':
    chrome_client = ChromeRemote()
    tabs = chrome_client.get_tabs()

    answers = ["{} - {}".format(x['title'].encode('utf-8'), x['url'][0:15]) for x in tabs]
    choice = Choice(title="Choose target tab:", answers=answers).ask()

    target_id = tabs[choice[0]]['id']
    chrome_client.choose_tab(target_id=target_id)
    import time
    time.sleep(1)

    chrome_client.session.send('Console.enable')
    chrome_client.session.send('Debugger.enable')

    chrome_client.session.on('Console.messageAdded', console_log)

    command_factory = ExecutorFactory(chrome_client=chrome_client)

    output_factory = OutputHandlerFactory(chrome_client)
    from console import Cmd
    for command in Cmd().cmd_generator():
        result = command_factory.execute(command)
        __import__('ipdb').set_trace()
        output = output_factory.process(result['result']) or {}
        pretty_print(**output)


