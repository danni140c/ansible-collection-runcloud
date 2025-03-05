#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_server

short_description: Manage RunCloud servers

version_added: "0.0.6"

description: Manage RunCloud servers through the RunCloud API

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


class RCServer(object):
    def __init__(self, module):
        self.rest = RunCloudHelper(module)
        self.module = module
        self.wait_timeout = self.module.params.pop("wait_timeout", 120)
        self.name = self.module.params.pop("name")
        self.ip_address = self.module.params.pop("ip_address")
        self.provider = self.module.params.pop("provider")
        self.php_version = RunCloudHelper.php_versions.get(
            self.module.params.pop("php_version")
        )
        self.paswordless_login = self.module.params.pop("passwordless_login")
        self.use_dns = self.module.params.pop("use_dns")
        self.prevent_root_login = self.module.params.pop("prevent_root_login")
        self.software_update = self.module.params.pop("software_update")
        self.security_update = self.module.params.pop("security_update")
        self.module.params.pop("api_key")
        self.module.params.pop("api_secret")

    def create(self):
        servers = self.rest.get_all_pages("servers")
        changed = False
        server = None

        for fetched_server in servers:
            if fetched_server.get("ipAddress", "") == self.ip_address:
                server = fetched_server
                break

        if server is None:
            request_data = dict(
                name=self.name,
                ipAddress=self.ip_address,
                provider=self.provider,
            )
            response = self.rest.post("servers", data=request_data)
            changed = True
            server = response.json

        server_id = server.get("id")

        if server.get("connected") == False:
            script = self.rest.get("servers/%s/installationscript" % (server_id)).json.get("script")
            self.module.run_command(args=script, use_unsafe_shell=True)
            changed = True

        if server.get("phpCLIVersion") != self.php_version:
            request_data = dict(
                phpVersion=self.php_version,
            )
            response = self.rest.patch(
                "servers/%s/php/cli" % (server_id), data=request_data
            )
            changed = True

        ssh_config = self.rest.get("servers/%s/settings/ssh" % (server_id)).json

        if (
            ssh_config.get("passwordlessLogin") != self.paswordless_login
            or ssh_config.get("useDns") != self.use_dns
            or ssh_config.get("preventRootLogin") != self.prevent_root_login
        ):
            request_data = dict(
                passwordlessLogin=self.paswordless_login,
                useDns=self.use_dns,
                preventRootLogin=self.prevent_root_login,
            )
            response = self.rest.patch(
                "servers/%s/settings/ssh" % (server_id), data=request_data
            )
            changed = True

        if server.get("name") != self.name or server.get("provider") != self.provider:
            request_data = dict(
                name=self.name,
                provider=self.provider,
            )
            response = self.rest.patch(
                "servers/%s/settings/meta" % (server_id), data=request_data
            )
            changed = True

        if (
            server.get("softwareUpdate") != self.software_update
            or server.get("securityUpdate") != self.security_update
        ):
            request_data = dict(
                softwareUpdate=self.software_update,
                securityUpdate=self.security_update,
            )
            response = self.rest.patch(
                "servers/%s/settings/autoupdate" % (server_id), data=request_data
            )
            changed = True

        server = self.rest.get("servers/%s" % (server_id)).json

        self.module.exit_json(
            changed=changed,
            data={"server": server},
        )

    def delete(self):
        return None


def core(module):
    state = module.params.pop("state")
    server = RCServer(module)
    if state == "present":
        server.create()
    elif state == "absent":
        server.delete()


def main():
    argument_spec = RunCloudHelper.runcloud_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True),
        state=dict(choices=["present", "absent"], default="present"),
        install_script=dict(type="bool", required=False, default=True),
        ip_address=dict(type="str", required=True),
        provider=dict(type="str", required=False, default="digitalocean"),
        php_version=dict(choices=["7.4", "8.0", "8.1", "8.2", "8.3"], required=True),
        passwordless_login=dict(type="bool", required=False, default=False),
        use_dns=dict(type="bool", required=False, default=False),
        prevent_root_login=dict(type="bool", required=False, default=True),
        software_update=dict(type="bool", required=False, default=False),
        security_update=dict(type="bool", required=False, default=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    core(module)


if __name__ == "__main__":
    main()
