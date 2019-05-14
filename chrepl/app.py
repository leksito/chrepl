from functools import wraps

from chrepl.console import Choice
from chrepl.common.util import locked_print
from chrepl.chrome_remote import ChromeRemote

from termcolor import colored

import abc, sys, json, re

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JavascriptLexer, HtmlLexer


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

    def process_node(self, result):
        class_name = result['className']

        object_id = result['objectId']
        node = chrome_client.session.send('DOM.describeNode', objectId=object_id)['node']

        local_name = node['localName']

        attrs = node['attributes']
        attrs = " ".join(["{}=\"{}\"".format(attrs[i], attrs[i+1]) for i in range(0, len(attrs), 2)])
        value = "<{} {}>".format(local_name, attrs)

        #highlight node

        highlightConfig = {
            "showInfo": True,
            "showRulers":False,
            "showExtensionLines":False,
            "contentColor":{"r":111,"g":168,"b":220,"a":0.66},
            "paddingColor":{"r":147,"g":196,"b":125,"a":0.55},
            "borderColor":{"r":255,"g":229,"b":153,"a":0.66},
            "marginColor":{"r":246,"g":178,"b":107,"a":0.66},
            "eventTargetColor":{"r":255,"g":196,"b":196,"a":0.66},
            "shapeColor":{"r":96,"g":82,"b":177,"a":0.8},
            "shapeMarginColor":{"r":96,"g":82,"b":127,"a":0.6},
            "displayAsMaterial":True
        };

        chrome_client.session.send("DOM.highlightNode", objectId=object_id,
            highlightConfig=highlightConfig)

        return {
            'class_name': class_name,
            'value': value
        }

    def process(self, result):
        subtype = result.get('subtype', None)
        if subtype and subtype == 'error':
            return self.process_error(result)
        elif subtype and subtype == 'node':
            return self.process_node(result)
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
        locked_print(" < " + message['text'])
    elif message['level'] == 'warning':
        text = colored(" < " + message['text'], 'yellow')
        locked_print(text)
    elif message['level'] == 'error':
        text = colored(" < " + message['text'], 'red')
        locked_print(text)
    elif message['level'] == 'debug':
        text = colored(" < " + message['text'], 'green')
        locked_print(text)
    elif message['level'] == 'info':
        text = colored(" < " + message['text'], 'blue')
        locked_print(text)


js_lexer = JavascriptLexer()
html_lexer = HtmlLexer()
formatter = TerminalFormatter()

def pretty_print(class_name=None, value=None):
    class_name = colored("[ {} ]".format(class_name), 'yellow') if class_name else None
    if type(value) == dict:
        value = json.dumps(value)
    lexer = html_lexer if "HTML" in class_name else js_lexer
    value = highlight(str(value), lexer, formatter)[:-1]
    output = filter(lambda out: out != None, [class_name, value])
    locked_print(" ".join(output))


def run():
    chrome_client = ChromeRemote()
    tabs = chrome_client.get_tabs()

    # answers = ["{} {}".format(x['title'].encode('utf-8')[:25], colored(x['url'], 'blue')) for x in tabs]
    answers = []
    for tab in tabs:
        name = colored(tab['title'].encode('utf-8')[:25], attrs=['bold'])
        url = colored(tab['url'], 'blue')
        answer = "{} - {}".format(name, url)
        answers.append(answer)


    choice = Choice(title="Choose target tab:", answers=answers).ask()

    target_id = tabs[choice[0]]['id']
    chrome_client.choose_tab(target_id=target_id)
    import time
    time.sleep(1)

    chrome_client.session.send('Console.enable')
    chrome_client.session.send('Debugger.enable')
    chrome_client.session.send('DOM.enable')

    chrome_client.session.on('Console.messageAdded', console_log)

    command_factory = ExecutorFactory(chrome_client=chrome_client)

    output_factory = OutputHandlerFactory(chrome_client)
    from console import Cmd
    for command in Cmd().cmd_generator():
        result = command_factory.execute(command)
        output = output_factory.process(result['result']) or {}
        pretty_print(**output)


