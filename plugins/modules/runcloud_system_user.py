#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_system_user

short_description: Manage RunCloud system users

version_added: "0.0.6"

description: Manage RunCloud system users through the RunCloud API

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


class RCSystemUser(object):
    def __init__(self, module):
        self.rest = RunCloudHelper(module)
        self.module = module
        self.wait_timeout = self.module.params.pop("wait_timeout", 120)
        self.server_id = self.module.params.pop("server_id", None)
        self.server_name = self.module.params.pop("server_name", None)
        self.username = self.module.params.pop("username")
        self.password = self.module.params.pop("password")
        self.module.params.pop("api_key")
        self.module.params.pop("api_secret")
        self.server_id = self.rest.get_server_id(
            server_name=self.server_name, server_id=self.server_id
        )

    def create(self):
        users = self.rest.get_all_pages("servers/%s/users" % (self.server_id))
        changed = False
        user = None

        for fetched_user in users:
            if fetched_user.get("username", "") == self.username:
                user = fetched_user
                break

        if user is None:
            request_data = dict(
                username=self.username,
                password=self.password,
            )
            response = self.rest.post(
                "servers/%s/users" % self.server_id, data=request_data
            )
            changed = True
            user = response.json

        self.module.exit_json(
            changed=changed,
            data={"user": user},
        )

    def delete(self):
        users = self.rest.get_all_pages("servers/%s/users" % (self.server_id))
        changed = False
        user = None

        for fetched_user in users:
            if fetched_user.get("username", "") == self.username:
                user = fetched_user
                break

        if user is None:
            self.module.exit_json(
                changed=changed,
            )

        self.rest.delete("servers/%s/users/%s" % (self.server_id, user.get("id")))
        changed = True
        self.module.exit_json(
            changed=changed,
        )


def core(module):
    state = module.params.pop("state")
    server = RCSystemUser(module)
    if state == "present":
        server.create()
    elif state == "absent":
        server.delete()


def main():
    argument_spec = RunCloudHelper.runcloud_argument_spec()
    argument_spec.update(
        server_id=dict(type="str", required=False),
        server_name=dict(type="str", required=False),
        state=dict(choices=["present", "absent"], default="present"),
        username=dict(type="str", required=True),
        password=dict(type="str", required=False, no_log=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[("server_id", "server_name")],
        supports_check_mode=False,
    )

    core(module)


if __name__ == "__main__":
    main()
