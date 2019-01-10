import pychrome
import requests


class Target:

    def __init__(self, host='http://localhost', port='9222'):
        self.chrome = pychrome.Browser("{}:{}".format(host, port))

    def list_tab(self):
        response = requests.get("%s/json" % self.chrome.dev_url, json=True)
        return response.json()

    def attach_to(self, target_id):
        pass

    def attach_to_active_tab(self):
        pass

import ipdb; ipdb.set_trace()

target = Target()
target.chrome.activate_tab

target.list_tab()

print("Done")
