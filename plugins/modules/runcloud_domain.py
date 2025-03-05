#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_domain

short_description: Manage RunCloud domains

version_added: "0.0.9"

description: Manage RunCloud domains through the RunCloud API

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


class RCDomain(object):
    def __init__(self, module):
        self.rest = RunCloudHelper(module)
        self.module = module
        self.wait_timeout = self.module.params.pop("wait_timeout", 120)
        self.server_id = self.module.params.pop("server_id", None)
        self.server_name = self.module.params.pop("server_name", None)
        self.webapp_id = self.module.params.pop("webapp_id", None)
        self.webapp_name = self.module.params.pop("webapp_name", None)
        self.name = self.module.params.pop("name")
        self.www = self.module.params.pop("www", False)
        self.redirection = self.module.params.pop("redirection")
        self.type = self.module.params.pop("type")
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


    def create_domain(self):
        request_data = dict(
            name=self.name,
            www=self.www,
            redirection=self.redirection,
            type=self.type,
        )
        response = self.rest.post("servers/%s/webapps/%s/domains" % (self.server_id, self.webapp_id), data=request_data)
        return response.json


    def create(self):
        changed = False
        domain = None

        domains = self.rest.get_all_pages("servers/%s/webapps/%s/domains" % (self.server_id, self.webapp_id))
        for fetched_domain in domains:
            if fetched_domain.get("name", "") == self.name:
                domain = fetched_domain
                break

        if domain is None:
            changed = True
            domain = self.create_domain()
        elif bool(domain.get("www")) != self.www \
            or domain.get("redirection") != self.redirection \
            or domain.get("type") != self.type:
            changed = True
            domain = self.create_domain()

        self.module.exit_json(
            changed=changed,
            data={"domain": domain},
        )

    def delete(self):
        self.module.exit_json(
            changed=False,
            data={}
        )
        return None


def core(module):
    state = module.params.pop("state")
    server = RCDomain(module)
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
        state=dict(choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True),
        www=dict(type="bool", default=False),
        redirection=dict(choices=["none", "www", "non-www"], default="none"),
        type=dict(choices=["alias", "primary", "redirect"], default="alias"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[("server_id", "server_name"), ("webapp_id", "webapp_name")],
        supports_check_mode=False,
    )

    core(module)


if __name__ == "__main__":
    main()

