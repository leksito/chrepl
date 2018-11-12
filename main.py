import PyChromeDevTools

import subprocess
import os, signal


class ChromeRunner:

    """ChromeRunner - runs chrome instance"""

    def __init__(self, listen_port):
        """ 
        :listen_port: remote debugging port

        """
        pid = os.fork()
        if pid == 0:
            self._child_process(listen_port)
        else:
            self.chrome_pid = pid
            self._parent_process()

    def _child_process(self, listen_port):
        args = [ "google-chrome", "--headless",
            "--remote-debugging-port={}".format(listen_port),
        ]
        subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os._exit(0)

    def _parent_process(self):
        def kill_chrome(sig, frame):
            self.kill()
            os._exit(1)
        signal.signal(signal.SIGINT, kill_chrome)

    def kill(self):
        try:
            os.kill(self.chrome_pid, signal.SIGKILL)
            os.waitpid(self.chrome_pid, os.WNOHANG)
        except:
            pass


chrome_runner = ChromeRunner(listen_port=9229)
chrome_runner.kill()


class REPL:
    def __init__(self):
        pass

