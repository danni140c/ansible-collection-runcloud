#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: runcloud_web_application

short_description: Manage RunCloud web applications

version_added: "0.0.6"

description: Manage RunCloud web applications through the RunCloud API

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


class RCWebApplication(object):
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
        self.rest = RunCloudHelper(module)
        self.module = module
        self.wait_timeout = self.module.params.pop("wait_timeout", 120)
        self.server_id = self.module.params.pop("server_id")
        self.name = self.module.params.pop("name")
        self.domains = self.module.params.pop("domains")
        self.user = self.module.params.pop("user")
        self.public_path = self.module.params.pop("public_path")
        self.php_version = RCWebApplication.php_versions.get(
            self.module.params.pop("php_version")
        )
        self.stack = self.module.params.pop("stack")
        self.stack_mode = self.module.params.pop("stack_mode")
        self.clickjacking_protection = self.module.params.pop("clickjacking_protection")
        self.xss_protection = self.module.params.pop("xss_protection")
        self.mime_sniffing_protection = self.module.params.pop(
            "mime_sniffing_protection"
        )
        self.process_manager = self.module.params.pop("process_manager")
        self.process_manager_start_servers = self.module.params.pop(
            "process_manager_start_servers"
        )
        self.process_manager_min_spare_servers = self.module.params.pop(
            "process_manager_min_spare_servers"
        )
        self.process_manager_max_spare_servers = self.module.params.pop(
            "process_manager_max_spare_servers"
        )
        self.process_manager_max_children = self.module.params.pop(
            "process_manager_max_children"
        )
        self.process_manager_max_requests = self.module.params.pop(
            "process_manager_max_requests"
        )
        self.open_basedir = self.module.params.pop(
            "open_basedir",
        )
        self.timezone = self.module.params.pop("timezone")
        self.disable_functions = self.module.params.pop("disable_functions")
        self.max_execution_time = self.module.params.pop("max_execution_time")
        self.max_input_time = self.module.params.pop("max_input_time")
        self.max_input_vars = self.module.params.pop("max_input_vars")
        self.memory_limit = self.module.params.pop("memory_limit")
        self.post_max_size = self.module.params.pop("post_max_size")
        self.upload_max_filesize = self.module.params.pop("upload_max_filesize")
        self.session_gc_maxlifetime = self.module.params.pop("session_gc_maxlifetime")
        self.allow_url_fopen = self.module.params.pop("allow_url_fopen")
        self.module.params.pop("api_key")
        self.module.params.pop("api_secret")

        if self.open_basedir is None:
            self.open_basedir = "/home/%s/webapps/%s:/var/lib/php/session:/tmp" % (
                self.user,
                self.name,
            )

    def create(self):
        webapps = self.rest.get_all_pages("servers/%s/webapps" % (self.server_id))
        changed = False
        webapp = None

        for fetched_webapp in webapps:
            if fetched_webapp.get("name", "") == self.name:
                webapp = fetched_webapp
                break

        if webapp is None:
            request_data = dict(
                name=self.name,
                domainName="ansible-test.era.dk",
                user=self.user,
                publicPath=self.public_path,
                phpVersion=self.php_version,
                stack=self.stack,
                stackMode=self.stack_mode,
                clickjackingProtection=self.clickjacking_protection,
                xssProtection=self.xss_protection,
                mimeSniffingProtection=self.mime_sniffing_protection,
                processManager=self.process_manager,
                processManagerStartServers=self.process_manager_start_servers,
                processManagerMinSpareServers=self.process_manager_min_spare_servers,
                processManagerMaxSpareServers=self.process_manager_max_spare_servers,
                processManagerMaxChildren=self.process_manager_max_children,
                processManagerMaxRequests=self.process_manager_max_requests,
                openBasedir=self.open_basedir,
                timezone=self.timezone,
                disableFunctions=self.disable_functions,
                maxExecutionTime=self.max_execution_time,
                maxInputTime=self.max_input_time,
                maxInputVars=self.max_input_vars,
                memoryLimit=self.memory_limit,
                postMaxSize=self.post_max_size,
                uploadMaxFilesize=self.upload_max_filesize,
                sessionGcMaxlifetime=self.session_gc_maxlifetime,
                allowUrlFopen=self.allow_url_fopen,
            )
            response = self.rest.post(
                "servers/%s/webapps/custom" % (self.server_id), data=request_data
            )
            changed = True
            webapp = response.json

        self.module.exit_json(
            changed=changed,
            data={"webapp": webapp},
        )

    def delete(self):
        return None


def core(module):
    state = module.params.pop("state")
    server = RCWebApplication(module)
    if state == "present":
        server.create()
    elif state == "absent":
        server.delete()


def main():
    argument_spec = RunCloudHelper.runcloud_argument_spec()
    argument_spec.update(
        server_id=dict(type="int"),
        server_name=dict(type="str"),
        id=dict(type="int"),
        name=dict(type="str"),
        domains=dict(type="list", elements="str", required=True),
        user=dict(type="str", required=True),
        public_path=dict(type="str", default=None, required=False),
        php_version=dict(choices=["7.4", "8.0", "8.1", "8.2", "8.3"], default="8.1"),
        stack=dict(
            choices=["hybrid", "nativenginx", "customnginx"], default="customnginx"
        ),
        stack_mode=dict(choices=["production", "development"], default="production"),
        clickjacking_protection=dict(type="bool", default=True),
        xss_protection=dict(type="bool", default=True),
        mime_sniffing_protection=dict(type="bool", default=True),
        process_manager=dict(
            choices=["dynamic", "ondemand", "static"], default="dynamic"
        ),
        process_manager_start_servers=dict(type="int", default=1),
        process_manager_min_spare_servers=dict(type="int", default=1),
        process_manager_max_spare_servers=dict(type="int", default=1),
        process_manager_max_children=dict(type="int", default=5),
        process_manager_max_requests=dict(type="int", default=500),
        open_basedir=dict(type="str", default=None, required=False),
        timezone=dict(type="str", default="UTC"),
        disable_functions=dict(
            type="str",
            default="getmyuid,passthru,leak,listen,diskfreespace,tmpfile,link,ignore_user_abort,shell_exec,dl,set_time_limit,exec,system,highlight_file,source,show_source,fpassthru,virtual,posix_ctermid,posix_getcwd,posix_getegid,posix_geteuid,posix_getgid,posix_getgrgid,posix_getgrnam,posix_getgroups,posix_getlogin,posix_getpgid,posix_getpgrp,posix_getpid,posix_getppid,posix_getpwuid,posix_getrlimit,posix_getsid,posix_getuid,posix_isatty,posix_kill,posix_mkfifo,posix_setegid,posix_seteuid,posix_setgid,posix_setpgid,posix_setsid,posix_setuid,posix_times,posix_ttyname,posix_uname,proc_open,proc_close,proc_nice,proc_terminate,escapeshellcmd,ini_alter,popen,pcntl_exec,socket_accept,socket_bind,socket_clear_error,socket_close,socket_connect,symlink,posix_geteuid,ini_alter,socket_listen,socket_create_listen,socket_read,socket_create_pair,stream_socket_server",
        ),
        max_execution_time=dict(type="int", default=30),
        max_input_time=dict(type="int", default=60),
        max_input_vars=dict(type="int", default=1000),
        memory_limit=dict(type="int", default=256),
        post_max_size=dict(type="int", default=256),
        upload_max_filesize=dict(type="int", default=256),
        session_gc_maxlifetime=dict(type="int", default=256),
        allow_url_fopen=dict(type="bool", default=True),
        state=dict(choices=["present", "absent"], default="present"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(["server_id", "server_name"], ["id", "name"]),
        required_if=(
            [
                (
                    "process_manager",
                    "dynamic",
                    [
                        "process_manager_start_servers",
                        "process_manager_min_spare_servers",
                        "process_manager_max_spare_servers",
                    ],
                )
            ]
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == "__main__":
    main()
