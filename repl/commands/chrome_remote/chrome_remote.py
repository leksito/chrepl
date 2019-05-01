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

class ReceiveLoop(threading.Thread):

    def __init__(self, ws, event_handlers={},
            method_results={}, stopped=threading.Event()):

        threading.Thread.__init__(self)

        self._ws = ws
        self.event_handlers = event_handlers
        self.method_results = method_results
        self._stopped = stopped
        self._stopped.clear()

    def _process_event(self, event):
        handler = self.event_handlers.get(event['method'], None)
        handler and handler(**event['params'])

    def _process_message(self, message):
        if "method" in message:
            self._process_event(message)
        elif "id" in message and message["id"] in self.method_results:
            self.method_results[message["id"]].put(message)

    def run(self):
        while not self._stopped.is_set():
            try:
                message = json.loads(self._ws.recv())
                print(message)
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
        self.receive_loop = ReceiveLoop(self._ws)
        self.receive_loop.start()

        def attached_target(**kwargs):
            session_id = kwargs.get("sessionId", None)
            print  session_id
            self.session = Session(session_id, self)
            print("Attached to tab. SessionID: {}".format(self.session.id))

        def detached_target(**kwargs):
            pass

        self.on('Target.attachedToTarget', attached_target)
        self.on('Target.detachedFromTarget', detached_target)



    def on(self, event, callback):
        if not callable(callback):
            raise RuntimeException("callback should be callable")

        self.receive_loop.event_handlers[event] = callback
        return True

    def delete_listener(self, event):
        return self.receive_loop.event_handlers.pop(event, None)

    def delete_all_listeners(self):
        self.receive_loop.event_handlers = {}
        return True

    def send(self, method, block=True, timeout=None, **params):
        self.action_id += 1
        self.receive_loop.method_results[self.action_id] = queue.Queue()
        self._ws.send(json.dumps({
            'id': self.action_id,
            'method': method,
            'params': params
        }))
        try:
            return self.receive_loop.method_results[self.action_id].get(
                block=block, timeout=timeout)
        except queue.Empty:
            return None


    def attach_to_browser_target(self):
        # it does not work
        # https://github.com/ChromeDevTools/devtools-protocol/issues/160
        self.send('Target.attachToBrowserTarget')

    def get_tabs(self):
        rp = requests.get("{}/json/list".format(self.dev_url), json=True)
        return [ tab for tab in rp.json() if tab['type'] == 'page' ]

    def choose_tab(self, target_id):
        self.send('Target.attachToTarget', targetId=target_id)


class Session:
    """Tab session"""

    def __init__(self, session_id, browser):
        self.id = session_id
        self.browser = browser
        self.action_id = 0
        self.results = queue.Queue()

        def receive_result(**kwargs):
            session_id = kwargs.get('sessionId', '')
            if not session_id or session_id != self.id:
                raise RuntimeException("Wrong session id")
            message = kwargs.get('message', None)
            self.results.put(message)

        self.browser.on('Target.receivedMessageFromTarget', receive_result)
        self.send("Console.enable", block=False)

    def send(self, method, block=True, timeout=None, **params):
        self.action_id += 1

        message = json.dumps({
            'id': self.action_id,
            'method': method,
            'params': params
        })
        self.browser.send('Target.sendMessageToTarget', block=block,
                          sessionId=self.id, message=message)
        try:
            return self.results.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def evaluate(self, expression):
        return self.send('Runtime.evaluate', expression=expression)


if __name__ == '__main__':
    cr = ChromeRemote()

    import ipdb; ipdb.set_trace()

    tabs = cr.get_tabs()
    target_id = tabs[0]['id']

    cr.choose_tab(target_id)

    cr.session.send('Page.navigate', url="https://www.tut.by")

    print("done")
