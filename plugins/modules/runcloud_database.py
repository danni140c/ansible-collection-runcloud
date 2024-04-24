#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_database

short_description: Manage RunCloud databases

version_added: "0.0.6"

description: Manage RunCloud databases through the RunCloud API

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


class RCDatabase(object):
    def __init__(self, module):
        self.rest = RunCloudHelper(module)
        self.module = module
        self.module.params.pop("api_key")
        self.module.params.pop("api_secret")
        self.server_id = self.module.params.pop("server_id")
        self.server_name = self.module.params.pop("server_name")
        self.name = self.module.params.pop("name")
        self.collation = self.module.params.pop("collation")
        self.users = self.module.params.pop("users")

    def create(self):
        databases = self.rest.get_all_pages("servers/%s/databases" % (self.server_id))
        changed = False
        database = None

        for fetched_database in databases:
            if fetched_database.get("name", "") == self.name:
                database = fetched_database
                break

        if database is None:
            request_data = dict(name=self.name, collation=self.collation)
            response = self.rest.post(
                "servers/%s/databases" % (self.server_id), data=request_data
            )
            changed = True
            database = response.json

        fetched_db_users = self.rest.get_all_pages("servers/%s/databaseusers" % (self.server_id))
        db_users = []

        for fetched_db_user in fetched_db_users:
            if fetched_db_user.get("username") in self.users:
                db_users.append(fetched_db_user)

        db_grants = self.rest.get_all_pages(
            "servers/%s/databases/%s/grant" % (self.server_id, database.get("id"))
        )

        for db_user in db_users:
            create = True
            for db_grant in db_grants:
                if db_user.get("id") == db_grant.get("id"):
                    create = False
                    break
            if create:
                request_data = dict(id=db_user.get("id"))
                self.rest.post(
                    "servers/%s/databases/%s/grant"
                    % (self.server_id, database.get("id")),
                    data=request_data,
                )
                changed = True

        for db_grant in db_grants:
            revoke = True
            for db_user in db_users:
                if db_grant.get("id") == db_user.get("id"):
                    revoke = False
                    break
            if revoke:
                request_data = dict(id=db_grant.get("id"))
                self.rest.delete(
                    "servers/%s/databases/%s/grant"
                    % (self.server_id, database.get("id")),
                    data=request_data,
                )
                changed = True

        self.module.exit_json(
            changed=changed,
            data={"database": database},
        )

    def delete(self):
        return None


def core(module):
    state = module.params.pop("state")
    server = RCDatabase(module)
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
        name=dict(type="str", required=True),
        collation=dict(type="str", required=False, default="utf8_danish_ci"),
        users=dict(type="list", elements="str"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == "__main__":
    main()
