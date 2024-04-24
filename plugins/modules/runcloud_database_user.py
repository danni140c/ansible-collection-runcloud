#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_database_user

short_description: Manage RunCloud database users

version_added: "0.0.1"

description: Manage RunCloud database users through the RunCloud API

options:
    state:
        description:
            - The desired state of the database user.
            - V(present) will ensure the database user exists.
            - V(absent) will ensure the database user does not exist.
        default: present
        choices: ["present", "absent"]
        type: str
    username:
        description:
            - The name of the database user to operate on.
        type: str
        required: true
    password:
        description:
            - The password of the database user.
            - Required if O(state=present).
        type: str
extends_documentation_fragment:
- danni140c.runcloud.runcloud.documentation
- danni140c.runcloud.runcloud.server_documentation

author:
    - Daniel Rasmussen (@danni140c)
"""

EXAMPLES = r"""
- name: Ensure database exists on server using server name
  danni140c.runcloud.runcloud_database_user:
    server_name: My Server
    state: present
    username: db_user
    password: secret_db_password

- name: Ensure database does not exist on server using server ID
  danni140c.runcloud.runcloud_database_user:
    server_id: 113243546
    state: absent
    username: db_user
"""

RETURN = r"""
data:
    description: The original name param that was passed in.
    type: dictionary
    returned: changed
    sample:
        database_user:
            id: 59
            username: db_user
            created_at: "2024-06-21 07:49:43"
msg:
    description: Error message.
    type: str
    returned: fail
    sample: 'Failed to find server by name or ID.'
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.danni140c.runcloud.plugins.module_utils.runcloud import (
    RunCloudHelper,
)


class RCDatabaseUser(object):
    def __init__(self, module):
        self.rest = RunCloudHelper(module)
        self.module = module
        self.module.params.pop("api_key")
        self.module.params.pop("api_secret")
        self.server_id = self.module.params.pop("server_id", None)
        self.server_name = self.module.params.pop("server_name", None)
        self.username = self.module.params.pop("username")
        self.password = self.module.params.pop("password")
        self.server_id = self.rest.get_server_id(
            server_name=self.server_name, server_id=self.server_id
        )

    def create(self):
        db_users = self.rest.get_all_pages(
            "servers/%s/databaseusers" % (self.server_id)
        )
        changed = False
        db_user = None

        for fetched_db_user in db_users:
            if fetched_db_user.get("username", "") == self.username:
                db_user = fetched_db_user
                break

        if db_user is None:
            request_data = dict(
                username=self.username,
                password=self.password,
            )
            response = self.rest.post(
                "servers/%s/databaseusers" % (self.server_id), data=request_data
            )
            changed = True
            db_user = response.json

        self.module.exit_json(
            changed=changed,
            data={"database_user": db_user},
        )

    def delete(self):
        db_users = self.rest.get_all_pages(
            "servers/%s/databaseusers" % (self.server_id)
        )
        changed = False
        db_user = None

        for fetched_db_user in db_users:
            if fetched_db_user.get("username", "") == self.username:
                db_user = fetched_db_user
                break

        if db_user is None:
            self.module.exit_json(
                changed=changed,
            )

        self.rest.delete(
            "servers/%s/databaseusers/%s" % (self.server_id, db_user.get("id"))
        )
        changed = True
        self.module.exit_json(
            changed=changed,
        )


def core(module):
    state = module.params.pop("state")
    server = RCDatabaseUser(module)
    if state == "present":
        server.create()
    elif state == "absent":
        server.delete()


def main():
    argument_spec = RunCloudHelper.runcloud_argument_spec()
    argument_spec.update(
        server_id=dict(type="int", required=False),
        server_name=dict(type="str", required=False),
        state=dict(choices=["present", "absent"], default="present"),
        username=dict(type="str", required=True),
        password=dict(type="str", required=False, no_log=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(["server_id", "server_name"]),
        required_if=([("state", "present", ["password"])]),
        supports_check_mode=False,
    )

    core(module)


if __name__ == "__main__":
    main()
