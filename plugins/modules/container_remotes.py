#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, StackHPC
# Apache License, Version 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

DOCUMENTATION = r"""
---
module: container_remotes
short_description: Manage multiple container remotes of a pulp api server instance
description:
  - "This performs CRUD operations on multiple container remotes in a pulp api server instance concurrently."
options:
  remotes:
    description:
      - List of remotes to manage
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Name of the remote
        type: str
        required: true
      upstream_name:
        description:
          - Name of the upstream repository
        type: str
      url:
        description:
          - URL of the remote
        type: str
      policy:
        description:
          - Whether downloads should be performed immediately, or lazy.
        type: str
        choices:
          - immediate
          - on_demand
          - streamed
      exclude_tags:
        description:
          - A list of tags to exclude during sync
        type: list
        elements: str
      include_tags:
        description:
          - A list of tags to include during sync
        type: list
        elements: str
      headers:
        description:
          - Headers to send with requests
        type: list
        elements: dict
      remote_username:
        description:
          - Username for remote authentication
        type: str
      remote_password:
        description:
          - Password for remote authentication
        type: str
      ca_cert:
        description:
          - CA certificate for TLS validation
        type: str
      client_cert:
        description:
          - Client certificate for authentication
        type: str
      client_key:
        description:
          - Client key for authentication
        type: str
      tls_validation:
        description:
          - Whether to validate TLS certificates
        type: bool
      proxy_url:
        description:
          - Proxy URL
        type: str
      proxy_username:
        description:
          - Username for proxy authentication
        type: str
      proxy_password:
        description:
          - Password for proxy authentication
        type: str
      download_concurrency:
        description:
          - Number of concurrent downloads
        type: int
      rate_limit:
        description:
          - Rate limit for downloads
        type: int
      total_timeout:
        description:
          - Total timeout for operations
        type: float
      connect_timeout:
        description:
          - Connect timeout
        type: float
      sock_connect_timeout:
        description:
          - Socket connect timeout
        type: float
      sock_read_timeout:
        description:
          - Socket read timeout
        type: float
      max_retries:
        description:
          - Maximum number of retries
        type: int
      state:
        description:
          - Desired state of the remote
        type: str
        choices: ["present", "absent"]
        default: present
    required: true
  concurrency:
    description:
      - Maximum number of concurrent operations
    type: int
    default: 10
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Alex Welsh (@alex-welsh)
"""

EXAMPLES = r"""
- name: Create multiple container remotes
  stackhpc.pulp.container_remotes:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    remotes:
      - name: remote1
        upstream_name: upstream1
        url: https://registry.example.com/repo1
        policy: immediate
        state: present
      - name: remote2
        upstream_name: upstream2
        url: https://registry.example.com/repo2
        state: present

- name: Delete multiple container remotes
  stackhpc.pulp.container_remotes:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    remotes:
      - name: remote1
        state: absent
      - name: remote2
        state: absent
"""

RETURN = r"""
  remotes:
    description: List of container remote results
    type: list
    returned: always
    elements: dict
    contains:
      name:
        description: Name of the remote
        type: str
      remote:
        description: Remote details (when applicable)
        type: dict
      changed:
        description: Whether the remote was changed
        type: bool
      failed:
        description: Whether the operation failed
        type: bool
      msg:
        description: Error message if failed
        type: str
  msg:
    description: Summary of the overall operation failure
    type: str
    returned: on failure
"""


import traceback
import concurrent.futures

from ansible_collections.pulp.squeezer.plugins.module_utils.pulp_glue import PulpAnsibleModule

try:
    from pulp_glue.container.context import PulpContainerRemoteContext
    from pulp_glue.common.context import PulpContext
    from pulp_glue.common.openapi import BasicAuthProvider
    from pulp_glue.common import __version__ as pulp_glue_version

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpContainerRemoteContext = None
    PulpContext = None
    BasicAuthProvider = None
    pulp_glue_version = None


class PulpBatchRemoteAnsibleModule(PulpAnsibleModule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process_single_remote(self, remote_item):
        result = {
            "name": remote_item["name"],
            "changed": False,
            "failed": False,
            "msg": "",
        }
        try:
            # Create a separate PulpContext for each thread to avoid correlation ID conflicts
            auth_args = {}
            if self.params["username"]:
                auth_args["auth_provider"] = BasicAuthProvider(
                    username=self.params["username"],
                    password=self.params["password"],
                )

            pulp_ctx = PulpContext(
                api_root="/pulp/",
                api_kwargs=dict(
                    base_url=self.params["pulp_url"],
                    cert=self.params["user_cert"],
                    key=self.params["user_key"],
                    validate_certs=self.params["validate_certs"],
                    refresh_cache=self.params["refresh_api_cache"],
                    user_agent=f"Squeezer/{pulp_glue_version}",
                    **auth_args,
                ),
                background_tasks=False,
                timeout=self.params["timeout"],
                fake_mode=self.check_mode,
            )

            context = PulpContainerRemoteContext(pulp_ctx)
            natural_key = {"name": remote_item["name"]}
            desired_attributes = {}

            # Collect desired attributes from remote_item
            for key in [
                "upstream_name", "url", "policy", "exclude_tags", "include_tags",
                "headers", "ca_cert", "client_cert", "client_key", "tls_validation",
                "proxy_url", "proxy_username", "proxy_password", "download_concurrency",
                "rate_limit", "total_timeout", "connect_timeout", "sock_connect_timeout",
                "sock_read_timeout", "max_retries"
            ]:
                if key in remote_item and remote_item[key] is not None:
                    desired_attributes[key] = remote_item[key]

            # Handle auth
            if "remote_username" in remote_item and remote_item["remote_username"] is not None:
                desired_attributes["username"] = remote_item["remote_username"]
            if "remote_password" in remote_item and remote_item["remote_password"] is not None:
                desired_attributes["password"] = remote_item["remote_password"]

            state = remote_item.get("state", "present")
            if state == "present":
                desired_entity = desired_attributes
            elif state == "absent":
                desired_entity = None
            else:
                result["failed"] = True
                result["msg"] = f"Invalid state '{state}'"
                return result

            # Simulate the converge logic
            context.entity = natural_key
            changed, before, after = context.converge(desired_entity)
            if changed:
                result["changed"] = True
            if after is not None:
                # Sanitize sensitive data from the returned object
                if "password" in after:
                    del after["password"]
                if "proxy_password" in after:
                    del after["proxy_password"]
                if "client_key" in after:
                    del after["client_key"]
                result["remote"] = after
        except Exception as e:
            result["failed"] = True
            result["msg"] = str(e)
        return result

    def process_batch_remotes(self, remotes, concurrency=10):
        results = []
        overall_changed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.process_single_remote, remote_item) for remote_item in remotes]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result["changed"]:
                    overall_changed = True
                results.append(result)

        # Sort results by original order
        results.sort(key=lambda x, m={r["name"]: i for i, r in enumerate(remotes)}: m[x["name"]])

        if overall_changed:
            self.set_changed()
        self.set_result("remotes", results)
        if any(r["failed"] for r in results):
            self.fail_json(msg="One or more items failed", remotes=results)


def main():
    with PulpBatchRemoteAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "remotes": {
                "type": "list",
                "elements": "dict",
                "required": True,
                "options": {
                    "name": {"type": "str", "required": True},
                    "upstream_name": {"type": "str"},
                    "url": {"type": "str"},
                    "policy": {
                        "type": "str",
                        "choices": ["immediate", "on_demand", "streamed"],
                    },
                    "exclude_tags": {"type": "list", "elements": "str"},
                    "include_tags": {"type": "list", "elements": "str"},
                    "headers": {"type": "list", "elements": "dict"},
                    "remote_username": {"type": "str"},
                    "remote_password": {"type": "str", "no_log": True},
                    "ca_cert": {"type": "str"},
                    "client_cert": {"type": "str"},
                    "client_key": {"type": "str", "no_log": True},
                    "tls_validation": {"type": "bool"},
                    "proxy_url": {"type": "str"},
                    "proxy_username": {"type": "str"},
                    "proxy_password": {"type": "str", "no_log": True},
                    "download_concurrency": {"type": "int"},
                    "rate_limit": {"type": "int"},
                    "total_timeout": {"type": "float"},
                    "connect_timeout": {"type": "float"},
                    "sock_connect_timeout": {"type": "float"},
                    "sock_read_timeout": {"type": "float"},
                    "max_retries": {"type": "int"},
                    "state": {
                        "type": "str",
                        "choices": ["present", "absent"],
                        "default": "present",
                    },
                },
            },
            "concurrency": {"type": "int", "default": 10},
        },
    ) as module:
        module.process_batch_remotes(module.params["remotes"], module.params["concurrency"])


if __name__ == "__main__":
    main()
