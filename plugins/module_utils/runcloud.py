#!/usr/bin/python
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url

class Response(object):
    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(to_text(self.info["body"]))
            return None
        try:
            return json.loads(to_text(self.body))
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]

class RunCloudHelper:
    base_url = "https://manage.runcloud.io/api/v2"

    def __init__(self, module):
        self.module = module
        self.module.params.update({
            "url_username": module.params.get("api_key"),
            "url_password": module.params.get("api_secret"),
            "force_basic_auth": True,
        })
        self.base_url = module.params.get("base_url", RunCloudHelper.base_url)
        self.timeout = module.params.get("timeout", 120)
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

    def _url_builder(self, path):
        if path[0] == "/":
            path = path[1:]
        return "%s/%s" % (self.base_url, path)

    def send(self, method, path, data=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)

        if method == "DELETE":
            if data == "null":
                data = None

        resp, info = fetch_url(
            self.module,
            url,
            data=data,
            headers=self.headers,
            method=method,
            timeout=self.timeout,
        )

        return Response(resp, info)

    def get_all_pages(self, path, data=None):
        page = self.get(path, data).json
        page_data = page.get("data", [])
        pagination = page.get("meta", {}).get("pagination", {})
        total_pages = pagination.get("total_pages", 1)
        current_page = pagination.get("current_page", 1)

        while current_page < total_pages:
            current_page = current_page + 1
            page = self.get("%s?page=%s" % (path, current_page)).json
            page_data.append(page.get("data", []))

        return page_data

    def get(self, path, data=None):
        return self.send("GET", path, data)

    def put(self, path, data=None):
        return self.send("PUT", path, data)

    def post(self, path, data=None):
        return self.send("POST", path, data)

    def patch(self, path, data=None):
        return self.send("PATCH", path, data)

    def delete(self, path, data=None):
        return self.send("DELETE", path, data)

    @staticmethod
    def runcloud_argument_spec():
        return dict(
            base_url=dict(
                type="str", required=False, default="https://manage.runcloud.io/api/v2"
            ),
            api_key=dict(
                no_log=True,
                # Support environment variable for RunCloud API Key
                fallback=(
                    env_fallback,
                    ["RC_API_KEY", "RUNCLOUD_API_KEY"],
                ),
                required=False,
            ),
            api_secret=dict(
                no_log=True,
                # Support environment variable for RunCloud API Secret
                fallback=(
                    env_fallback,
                    ["RC_API_SECRET", "RUNCLOUD_API_SECRET"],
                ),
                required=False,
            ),
            timeout=dict(type="int", default=120),
        )