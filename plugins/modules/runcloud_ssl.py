#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_ssl

short_description: Manage RunCloud SSL

version_added: "0.0.9"

description: Manage RunCloud SSL through the RunCloud API

author:
    - Daniel Rasmussen (@danni140c)
"""

EXAMPLES = r"""
"""

RETURN = r"""
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.danni140c.runcloud.plugins.module_utils.runcloud import (
    RunCloudHelper,
)


class RCSsl(object):
    ssl_protocol_id = dict(
        [
            ("TLSv1.1", 1),
            ("TLSv1.2", 2),
            ("TLSv1.3", 3),
        ]
    )

    def __init__(self, module):
        self.rest = RunCloudHelper(module)
        self.module = module
        self.wait_timeout = self.module.params.pop("wait_timeout", 120)
        self.server_id = self.module.params.pop("server_id", None)
        self.server_name = self.module.params.pop("server_name", None)
        self.webapp_id = self.module.params.pop("webapp_id", None)
        self.webapp_name = self.module.params.pop("webapp_name", None)
        self.advanced = self.module.params.pop("advanced")
        self.auto = self.module.params.pop("auto")
        self.provider = self.module.params.pop("provider")
        self.enable_http = self.module.params.pop("enable_http")
        self.enable_hsts = self.module.params.pop("enable_hsts")
        self.protocol = RCSsl.ssl_protocol_id.get(
            self.module.params.pop("protocol")
        )
        self.authorization_method = self.module.params.pop("authorization_method")
        self.environment = self.module.params.pop("environment")
        self.module.params.pop("api_key")
        self.module.params.pop("api_secret")
        self.server_id = self.rest.get_id(
            url="servers",
            name_key="name",
            id_key="id",
            name_value=self.server_name,
            key_value=self.server_id,
        )
        self.webapp_id = self.rest.get_id(
            url="servers/%s/webapps" % (self.server_id),
            name_key="name",
            id_key="id",
            name_value=self.webapp_name,
            key_value=self.webapp_id,
        )

    def install_basic(self):
        request_data = dict(
            provider=self.provider,
            enableHttp=self.enable_http,
            enableHsts=self.enable_hsts,
            ssl_protocol_id=self.protocol,
            authorizationMethod=self.authorization_method,
            environment=self.environment
        )
        return self.rest.post("servers/%s/webapps/%s/ssl" % (self.server_id, self.webapp_id), data=request_data)

    def create(self):
        changed = False
        ssl = None

        response = self.rest.get("servers/%s/webapps/%s/ssl/advanced" % (self.server_id, self.webapp_id))
        ssl_advanced = response.json.get("advancedSSL", False)

        if ssl_advanced != self.advanced:
            request_data = dict(
                advancedSSL=self.advanced,
                autoSSL=self.auto,
            )
            response = self.rest.post("servers/%s/webapps/%s/ssl/advanced" % (self.server_id, self.webapp_id), data=request_data)
            ssl_advanced = response.json.get("advancedSSL", None)
            if ssl_advanced is None or ssl_advanced != self.advanced:
                self.module.fail_json(
                    msg="Failed to change SSL mode."
                )

        if self.advanced:
            self.webapp_id
        else:
            response = self.rest.get("servers/%s/webapps/%s/ssl" % (self.server_id, self.webapp_id))
            ssl = response.json
            ssl_not_installed = ssl.get("message", "") == "SSL not installed!"

            if ssl_not_installed:
                response = self.install_basic()
                ssl = response.json
                changed = True
            elif (
                ssl.get("enableHttp") != self.enable_http \
                or ssl.get("enableHsts") != self.enable_hsts \
                or ssl.get("ssl_protocol_id") != self.protocol \
                or (ssl.get("staging") == False and self.environment == "staging") \
                or (ssl.get("staging") == True and self.environment == "live")
            ):
                self.rest.delete("servers/%s/webapps/%s/ssl/%s" % (self.server_id, self.webapp_id, ssl.get("id")))
                response = self.install_basic()
                ssl = response.json
                changed = True

        self.module.exit_json(
            changed=changed,
            data={"ssl": ssl},
        )

    def delete(self):
        return None


def core(module):
    state = module.params.pop("state")
    server = RCSsl(module)
    if state == "present":
        server.create()
    elif state == "absent":
        server.delete()


def main():
    argument_spec = RunCloudHelper.runcloud_argument_spec()
    argument_spec.update(
        server_id=dict(type="int", required=False),
        server_name=dict(type="str", required=False),
        webapp_id=dict(type="int"),
        webapp_name=dict(type="str"),
        state=dict(choices=["present", "absent", "redeploy"], default="present"),
        advanced=dict(type="bool", default=False),
        auto=dict(type="bool", default=False),
        provider=dict(choices=["letsencrypt"], default="letsencrypt"),
        enable_http=dict(type="bool", default=False),
        enable_hsts=dict(type="bool", default=False),
        protocol=dict(choices=["TLSv1.1", "TLSv1.2", "TLSv1.3"], default="TLSv1.1"),
        authorization_method=dict(choices=["http-01"], default="http-01"),
        environment=dict(choices=["live", "staging"], default="live"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[("server_id", "server_name"), ("webapp_id", "webapp_name")],
        supports_check_mode=False,
    )

    core(module)


if __name__ == "__main__":
    main()

