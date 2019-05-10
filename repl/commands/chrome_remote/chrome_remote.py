import json
import time

import requests
import websocket
import threading

try:
    import Queue as queue
except ImportError:
    import queue

TIMEOUT = 5

class EventHandler(threading.Thread):

    def __init__(self, events, event_handlers, stopped):

        threading.Thread.__init__(self)

        self.events = events
        self.event_handlers = event_handlers
        self.stopped = stopped

    def run(self):
        while not self.stopped.is_set():
            event = self.events.get(block=True)
            handler = self.event_handlers.get(event['method'], None)
            handler and handler(**event['params'])


class ReceiveLoop(threading.Thread):

    def __init__(self, ws, events=queue.Queue(),
            method_results={}, stopped=threading.Event()):

        threading.Thread.__init__(self)

        self._ws = ws
        self.events = events
        self.method_results = method_results
        self.stopped = stopped
        self.stopped.clear()

    def _process_message(self, message):
        if "method" in message:
            self.events.put(message)
        elif "id" in message and message["id"] in self.method_results:
            self.method_results[message["id"]].put(message)

    def run(self):
        while not self.stopped.is_set():
            try:
                message = json.loads(self._ws.recv())
                self._process_message(message)
            except Exception as error:
                raise error


class ChromeRemote(object):

    def __init__(self, host='http://localhost', port=9222):
        self.dev_url = "{}:{}".format(host, port)
        rp = requests.get("{}/json/version".format(self.dev_url), json=True)

        self._ws_url = rp.json()["webSocketDebuggerUrl"]
        self._ws = websocket.create_connection(self._ws_url, enable_multithread=True)

        self.session = None
        self.action_id = 0

        self.receive_loop = ReceiveLoop(ws=self._ws)
        self.receive_loop.daemon = True
        self.receive_loop.start()

        self.event_handler = EventHandler(events=self.receive_loop.events,
            event_handlers={}, stopped=self.receive_loop.stopped)
        self.event_handler.daemon = True
        self.event_handler.start()

        def attached_target(**kwargs):
            session_id = kwargs.get("sessionId", None)
            self.session = Session(session_id, self)
            print("Attached to tab. SessionID: {}".format(self.session.id))

        def detached_target(**kwargs):
            import sys
            sys.exit(1)

        self.on('Target.attachedToTarget', attached_target)

        self.on('Target.detachedFromTarget', detached_target)

    def on(self, event, callback):
        if not callable(callback):
            raise RuntimeException("callback should be callable")

        self.event_handler.event_handlers[event] = callback
        return True

    def delete_listener(self, event):
        return self.event_handler.event_handlers.pop(event, None)

    def delete_all_listeners(self):
        self.event_handler.event_handlers = {}
        return True

    def send(self, method, block=True, timeout=None, **params):
        try:
            self.action_id += 1
            self.receive_loop.method_results[self.action_id] = queue.Queue()
            self._ws.send(json.dumps({
                'id': self.action_id,
                'method': method,
                'params': params
            }))
            return self.receive_loop.method_results[self.action_id].get(
                block=block, timeout=timeout)['result']
        except queue.Empty:
            return None
        finally:
            self.receive_loop.method_results.pop(self.action_id)

    def attach_to_browser_target(self):
        # it does not work
        # https://github.com/ChromeDevTools/devtools-protocol/issues/160
        self.send('Target.attachToBrowserTarget')

    def get_tabs(self):
        rp = requests.get("{}/json/list".format(self.dev_url), json=True)
        return [ tab for tab in rp.json() if tab['type'] == 'page' ]

    def choose_tab(self, target_id):
        self.send('Target.attachToTarget', targetId=target_id)


class SessionEventHandler(EventHandler):

    def __init__(self, *args, **kwargs):
        EventHandler.__init__(self, *args, **kwargs)

    def run(self):
        while not self.stopped.is_set():
            event = self.events.get(block=True)
            handler = self.event_handlers.get(event['method'], None)
            handler and handler(**event['params'])


class Session:
    """Tab session"""

    def __init__(self, session_id, browser):
        self.id = session_id
        self.browser = browser
        self.action_id = 0
        self.results = {}

        self.events = queue.Queue()

        def receive_result(**kwargs):
            session_id = kwargs.get('sessionId', '')
            if not session_id or session_id != self.id:
                raise RuntimeException("Wrong session id")
            message = json.loads(kwargs.get('message', None))

            if "method" in message:
                self.events.put(message)
            elif "id" in message and message["id"] in self.results:
                self.results[message["id"]].put(message)

        self.event_handler = SessionEventHandler(events=self.events,
            event_handlers={}, stopped=self.browser.receive_loop.stopped)
        self.event_handler.daemon = True
        self.event_handler.start()

        self.browser.on('Target.receivedMessageFromTarget', receive_result)

    def on(self, event, callback):
        if not callable(callback):
            raise RuntimeException("callback should be callable")

        self.event_handler.event_handlers[event] = callback
        return True

    def delete_listener(self, event):
        return self.event_handler.event_handlers.pop(event, None)

    def delete_all_listeners(self):
        self.event_handler.event_handlers = {}
        return True

    def send(self, method, block=True, timeout=None, **params):
        try:
            self.action_id += 1
            self.results[self.action_id] = queue.Queue()

            message = json.dumps({
                'id': self.action_id,
                'method': method,
                'params': params
            })
            self.browser.send('Target.sendMessageToTarget', block=block,
                            sessionId=self.id, message=message)
            result = self.results[self.action_id].get()
            print "Result:"
            print result
            return result['result']
        finally:
            self.results.pop(self.action_id)

    def evaluate(self, expression):
        return self.send('Runtime.evaluate', expression=expression)


if __name__ == '__main__':
    cr = ChromeRemote()


    tabs = cr.get_tabs()
    target_id = tabs[0]['id']

    cr.choose_tab(target_id)

    cr.session.send('Page.navigate', url="https://www.tut.by")
