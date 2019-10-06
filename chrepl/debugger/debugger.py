from chrepl.chrome_remote import ChromeRemote
import json

try:
    import Queue as queue
except ImportError:
    import queue

class Script:

    def __init__(self, chrome_client, script_json):
        self.chrome_client = chrome_client
        self.script = json.loads(script)

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            return self.script[name]
        return _missing

    def set_script_source(self, script_source):
        self.chrome_client.session.send('Debugger.setScriptSource', 
                scriptId=self.id, scriptSource=script_source)

    def script_source(self):
        return self.chrome_client.session.send(
                'Debugger.getScriptSource', scriptId=self.id())

    def show_part(self, line_number, column_number=None, lines_number=2):
        pass

    def get_posible_breakpoints(self):
        pass


class Debugger:

    def __init__(self, chrome_client):
        self.chrome_client = chrome_client
        self.chrome_client.session.send('Debugger.enable')

        self.parsed_scripts = []
        def save_parsed_script(**kwargs):
            self.parsed_scripts.append(Script(self.chrome_client, kwargs))
        self.chrome_client.on('Debugger.scriptParsed', save_parsed_script)

        self.breakpoints_is_active = True

        self.breakpoint_resolved = Queue()
        def breakpoint_resolved(**kwargs):
            self.breakpoint_resolved.put(kwargs)
        self.chrome_client.session.on('Debugger.breakpointResolved', breakpoint_resolved)

    def set_breakpoint(self, location, condition=None):
        pass

    def step_into(self):
        self.chrome_client.session.send('Debugger.stepInto')

    def step_out(self):
        self.chrome_client.session.send('Debugger.stepOut')

    def step_over(self):
        self.chrome_client.session.send('Debugger.stepOver')

    def toggle_breakpoints_active(self):
        self.breakpoints_is_active = self.chrome_client.session.send('Debugger.setBreakpointsActive')
