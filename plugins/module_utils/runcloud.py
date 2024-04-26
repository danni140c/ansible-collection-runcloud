#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c), Ansible Project 2017
# Simplified BSD License (see or https://opensource.org/licenses/BSD-2-Clause)

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

    php_versions = dict(
        [
            ("7.4", "php74rc"),
            ("8.0", "php80rc"),
            ("8.1", "php81rc"),
            ("8.2", "php82rc"),
            ("8.3", "php83rc"),
        ]
    )

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
            page_data.extend(page.get("data", []))

        return page_data

    # def get_paginated_data(
    #     self,
    #     base_url=None,
    #     data_key_name=None,
    #     data_per_page=40,
    #     expected_status_code=200,
    # ):
    #     """
    #     Function to get all paginated data from given URL
    #     Args:
    #         base_url: Base URL to get data from
    #         data_key_name: Name of data key value
    #         data_per_page: Number results per page (Default: 40)
    #         expected_status_code: Expected returned code from DigitalOcean (Default: 200)
    #     Returns: List of data

    #     """
    #     page = 1
    #     has_next = True
    #     ret_data = []
    #     status_code = None
    #     response = None
    #     while has_next or status_code != expected_status_code:
    #         required_url = "{0}page={1}&per_page={2}".format(
    #             base_url, page, data_per_page
    #         )
    #         response = self.get(required_url)
    #         status_code = response.status_code
    #         # stop if any error during pagination
    #         if status_code != expected_status_code:
    #             break
    #         page += 1
    #         ret_data.extend(response.json[data_key_name])
    #         try:
    #             has_next = (
    #                 "pages" in response.json["links"]
    #                 and "next" in response.json["links"]["pages"]
    #             )
    #         except KeyError:
    #             # There's a bug in the API docs: GET v2/cdn/endpoints doesn't return a "links" key
    #             has_next = False

    #     if status_code != expected_status_code:
    #         msg = "Failed to fetch %s from %s" % (data_key_name, base_url)
    #         if response:
    #             msg += " due to error : %s" % response.json["message"]
    #         self.module.fail_json(msg=msg)

    #     return ret_data

    def get_id(self, url=None, name_key=None, id_key=None, name_value=None, key_value=None):
        entities = self.get_all_pages(url)
        for entity in entities:
            if name_value is None and entity.get(id_key, 0) == key_value:
                break

            if key_value is None and entity.get(name_key, "") == name_value:
                key_value = entity.get(id_key, None)
                break

        if key_value is None:
            self.module.fail_json(
                msg="Failed to find server by name or ID."
            )

        return key_value

    def get_server_id(self, server_name=None, server_id=None):
        servers = self.get_all_pages("servers")
        for server in servers:
            if server_name is None and server.get("id", 0) == server_id:
                break

            if server_id is None and server.get("name", "") == server_name:
                server_id = server.get("id", None)
                break

        if server_id is None:
            self.module.fail_json(
                msg="Failed to find server by name or ID."
            )

        return server_id

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