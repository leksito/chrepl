import json
import time

import requests
import websocket
import threading
import pychrome

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
                self._process_message(message)
            except Exception as error:
                print('handling error: {}'.format(error))


class ChromeRemote(object):

    def __init__(self, host='http://localhost', port=9222):
        self.dev_url = "{}:{}".format(host, port)
        rp = requests.get("{}/json/version".format(self.dev_url), json=True)

        self._ws_url = rp.json()["webSocketDebuggerUrl"]
        self._ws = websocket.create_connection(self._ws_url, enable_multithread=True)

        self.session_id = None
        self.current_id = 1000
        self.receive_loop = ReceiveLoop(self._ws)
        self.receive_loop.start()

        def attached_target(**kwargs):
            self.session_id = kwargs.get("sessionId", None)
        
        def detached_target(**kwargs):
            self.session_id = None

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

    def send_to_session(self, method, **params):
        if not self.session_id:
            raise RuntimeException("session id is not specified, choose your target")
        self.current_id += 1
        self.receive_loop.method_results[self.current_id] = queue.Queue()
        message = json.dumps({
            'id': self.current_id,
            'method': 'Target.sendMessageToTarget',
            'params': {
                'message': {
                    'method': method,
                    'params': params
                },
                'sessionId': self.session_id
            }
        })
        print(message)
        self._ws.send(message)
        return self.receive_loop.method_results[self.current_id].get()

    def send_to_browser(self, method, **params):
        self.current_id += 1
        self.receive_loop.method_results[self.current_id] = queue.Queue()
        self._ws.send(json.dumps({
            'id': self.current_id,
            'method': method,
            'params': params
        }))
        return self.receive_loop.method_results[self.current_id].get()


cr = ChromeRemote()
import ipdb; ipdb.set_trace()
rs = cr.send_to_browser('Target.attachToBrowserTarget')
rs = cr.send_to_session('Page.navigate', url='http://www.tmall.com')
print("done")
