#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, StackHPC
# Apache License, Version 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

DOCUMENTATION = r"""
---
module: container_repositories
short_description: Manage multiple container repositories of a pulp api server instance
description:
  - "This performs CRUD operations on multiple container repositories in a pulp api server instance in a single call."
options:
  repositories:
    description:
      - List of repositories to manage
    type: list
    elements: dict
    required: true
    suboptions:
      name:
        description:
          - Name of the repository
        type: str
        required: true
      description:
        description:
          - Description of the repository
        type: str
      state:
        description:
          - Desired state of the repository
        type: str
        choices: ["present", "absent"]
        default: present
  concurrency:
    description:
      - Maximum number of concurrent operations
    type: int
    default: 10
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Mark Goddard (@markgoddard)
"""

EXAMPLES = r"""
- name: Create multiple container repositories
  stackhpc.pulp.container_repositories:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repositories:
      - name: repo1
        description: A brand new repository
        state: present
      - name: repo2
        description: Another repository
        state: present

- name: Create multiple container repositories with custom concurrency
  stackhpc.pulp.container_repositories:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    concurrency: 5
    repositories:
      - name: repo1
        description: A brand new repository
      - name: repo2
        description: Another repository

- name: Delete multiple container repositories
  stackhpc.pulp.container_repositories:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repositories:
      - name: repo1
        state: absent
      - name: repo2
        state: absent
"""

RETURN = r"""
  repositories:
    description: List of container repository results
    type: list
    returned: always
    elements: dict
    contains:
      name:
        description: Name of the repository
        type: str
      repository:
        description: Repository details (when applicable)
        type: dict
      changed:
        description: Whether the repository was changed
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
    from pulp_glue.container.context import PulpContainerRepositoryContext
    from pulp_glue.common.context import PulpContext
    from pulp_glue.common.openapi import BasicAuthProvider
    from pulp_glue.common import __version__ as pulp_glue_version
    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpContainerRepositoryContext = None
    PulpContext = None
    BasicAuthProvider = None
    pulp_glue_version = None


class PulpBatchRepositoryAnsibleModule(PulpAnsibleModule):
    def __init__(self, context_class, **kwargs):
        super().__init__(**kwargs)
        self.context_class = context_class

    def process_single_repository(self, entity):
        result = {
            "name": entity["name"],
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

            context = self.context_class(pulp_ctx)
            natural_key = {"name": entity["name"]}
            desired_attributes = {}
            if "description" in entity and entity["description"] is not None:
                desired_attributes["description"] = entity["description"]

            state = entity.get("state", "present")
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
                result["repository"] = after
        except Exception as e:
            result["failed"] = True
            result["msg"] = str(e)
        return result

    def process_batch_repositories(self, entities, concurrency=10):
        results = []
        overall_changed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.process_single_repository, entity) for entity in entities]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result["changed"]:
                    overall_changed = True
                results.append(result)

        # Sort results by original order
        results.sort(key=lambda x, m={e["name"]: i for i, e in enumerate(entities)}: m[x["name"]])

        if overall_changed:
            self.set_changed()
        self.set_result("repositories", results)
        if any(r["failed"] for r in results):
            self.fail_json(msg="One or more items failed", repositories=results)


def main():
    with PulpBatchRepositoryAnsibleModule(
        context_class=PulpContainerRepositoryContext,
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "repositories": {
                "type": "list",
                "elements": "dict",
                "options": {
                    "name": {"required": True},
                    "description": {},
                    "state": {"choices": ["present", "absent"], "default": "present"},
                },
                "required": True,
            },
            "concurrency": {"type": "int", "default": 10},
        },
    ) as module:
        module.process_batch_repositories(module.params["repositories"], module.params["concurrency"])


if __name__ == "__main__":
    main()
