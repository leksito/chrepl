from __future__ import annotations

import subprocess
import os, signal


class ChromeRunner:

    """ChromeRunner - runs chrome instance"""

    def __init__(self, listen_port: int):
        """ :listen_port: remote debugging port """

        pid = os.fork()
        if pid == 0:
            self.run_chrome_headless(listen_port)
        else:
            self.chrome_pid = pid
            self.register_sigint()

    def run_chrome_headless(self, listen_port: int):
        """ Runs child process - google-chrome --headless --remote-debuging-port=:listen_port
        :listen_port: remote debugging port
        """

        args = [ "google-chrome", "--headless",
            "--remote-debugging-port={}".format(listen_port),
        ]
        subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os._exit(0)

    def register_sigint(self):
        """ Register signal SIGINT to kill child process.  """

        def handle_sigint(*args, **kwargs):
            self.kill()
            os._exit(1)

        signal.signal(signal.SIGINT, handle_sigint)

    def kill(self):
        """ Kill child process.  """
        os.kill(self.chrome_pid, signal.SIGKILL)
        os.waitpid(self.chrome_pid, os.WNOHANG)
