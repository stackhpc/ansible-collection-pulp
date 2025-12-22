#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, StackHPC
# Apache License, Version 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

DOCUMENTATION = r"""
---
module: container_syncs
short_description: Synchronize multiple container remotes on a pulp server concurrently
description:
  - "This module synchronizes multiple container remotes into repositories concurrently."
  - "In check_mode this module assumes, nothing changed upstream."
options:
  syncs:
    description:
      - List of sync operations to perform
    type: list
    elements: dict
    suboptions:
      remote:
        description:
          - Name of the remote to synchronize
        type: str
        required: false
      repository:
        description:
          - Name of the repository
        type: str
        required: true
      timeout:
        description:
          - Timeout for the sync operation
        type: int
        default: 3600
    required: true
  concurrency:
    description:
      - Maximum number of concurrent sync operations
    type: int
    default: 10
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Alex Welsh (@alex-welsh)
"""

EXAMPLES = r"""
- name: Sync multiple container remotes into repositories
  stackhpc.pulp.container_syncs:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    syncs:
      - repository: repo_1
        remote: remote_1
      - repository: repo_2
        remote: remote_2
  register: sync_results

- name: Sync multiple repositories with custom concurrency
  stackhpc.pulp.container_syncs:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    concurrency: 5
    syncs:
      - repository: repo_1
      - repository: repo_2
        timeout: 7200
"""

RETURN = r"""
  syncs:
    description: List of sync operation results
    type: list
    returned: always
    elements: dict
    contains:
      repository:
        description: Name of the repository
        type: str
      repository_version:
        description: Repository version after syncing
        type: dict
      changed:
        description: Whether the sync changed the repository
        type: bool
      failed:
        description: Whether the sync operation failed
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
    from pulp_glue.container.context import (
        PulpContainerRemoteContext,
        PulpContainerRepositoryContext,
    )
    from pulp_glue.common.context import PulpContext
    from pulp_glue.common.openapi import BasicAuthProvider
    from pulp_glue.common import __version__ as pulp_glue_version

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpContainerRemoteContext = None
    PulpContainerRepositoryContext = None
    PulpContext = None
    BasicAuthProvider = None
    pulp_glue_version = None


class PulpBatchSyncAnsibleModule(PulpAnsibleModule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process_single_sync(self, sync_item):
        result = {
            "repository": sync_item["repository"],
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
                timeout=sync_item.get("timeout", 3600),
                fake_mode=self.check_mode,
            )

            repository_ctx = PulpContainerRepositoryContext(
                pulp_ctx, entity={"name": sync_item["repository"]}
            )
            repository = repository_ctx.entity

            payload = {}
            remote_name = sync_item.get("remote")
            if remote_name is None:
                if repository.get("remote") is None:
                    raise Exception(
                        "No remote was specified and none preconfigured on the repository."
                    )
            else:
                remote_ctx = PulpContainerRemoteContext(
                    pulp_ctx, entity={"name": remote_name}
                )
                payload["remote"] = remote_ctx

            repository_version = repository.get("latest_version_href")
            # In check_mode, assume nothing changed
            if not self.check_mode:
                sync_task = repository_ctx.sync(body=payload)

                if sync_task["created_resources"]:
                    result["changed"] = True
                    repository_version = sync_task["created_resources"][0]

            result["repository_version"] = repository_version
        except Exception as e:
            result["failed"] = True
            result["msg"] = str(e)
        return result

    def process_batch_syncs(self, syncs, concurrency=10):
        results = []
        overall_changed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.process_single_sync, sync_item) for sync_item in syncs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result["changed"]:
                    overall_changed = True
                results.append(result)

        # Sort results by original order
        results.sort(key=lambda x, m={s["repository"]: i for i, s in enumerate(syncs)}: m[x["repository"]])

        if overall_changed:
            self.set_changed()
        self.set_result("syncs", results)
        if any(r["failed"] for r in results):
            self.fail_json(msg="One or more items failed", syncs=results)


def main():
    with PulpBatchSyncAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "syncs": {
                "type": "list",
                "elements": "dict",
                "options": {
                    "remote": {},
                    "repository": {"required": True},
                    "timeout": {"type": "int", "default": 3600},
                },
                "required": True,
            },
            "concurrency": {"type": "int", "default": 10},
        },
    ) as module:
        module.process_batch_syncs(module.params["syncs"], module.params["concurrency"])


if __name__ == "__main__":
    main()
