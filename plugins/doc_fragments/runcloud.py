#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Daniel Rasmussen (@danni140c)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    # Parameters for RunCloud modules
    DOCUMENTATION = r"""
options:
  base_url:
    description:
      - RunCloud API base url.
    type: str
    default: https://manage.runcloud.io/api/v2
  api_key:
    description:
      - RunCloud API key.
      - "There are several other environment variables which can be used to provide this value."
      - "i.e., - E(RC_API_KEY) and C(RUNCLOUD_API_KEY)."
    type: str
  api_secret:
    description:
      - RunCloud API secret.
      - "There are several other environment variables which can be used to provide this value."
      - "i.e., - E(RC_API_SECRET) and C(RUNCLOUD_API_SECRET)."
    type: str
  timeout:
    description:
    - The timeout in seconds used for polling RunCloud's API.
    type: int
    default: 120
"""

    SERVER_DOCUMENTATION = r"""
options:
    server_id:
        description:
            - The server ID you want to operate on.
            - Required if O(server_name) is omitted.
        type: int
    server_name:
        description:
            - The server name you want to operate on.
            - Required if O(server_id) is omitted.
        type: str
"""