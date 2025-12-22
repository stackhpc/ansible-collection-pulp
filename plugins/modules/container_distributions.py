#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, StackHPC
# Apache License, Version 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

DOCUMENTATION = r"""
---
module: container_distributions
short_description: Manage multiple container distributions of a pulp api server instance
description:
  - "This performs CRUD operations on multiple container distributions in a pulp api server instance concurrently."
options:
  distributions:
    description:
      - List of distributions to manage
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Name of the distribution
        type: str
        required: true
      base_path:
        description:
          - Base path of the distribution
        type: str
      repository:
        description:
          - Repository name the distribution serves
        type: str
      version:
        description:
          - Repository version the distribution serves
        type: int
      content_guard:
        description:
          - Content guard to protect the distribution
        type: str
      private:
        description:
          - Whether the distribution is private
        type: bool
      state:
        description:
          - Desired state of the distribution
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
- name: Create multiple container distributions
  stackhpc.pulp.container_distributions:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    distributions:
      - name: dist1
        base_path: dist1
        repository: repo1
        state: present
      - name: dist2
        base_path: dist2
        repository: repo2
        private: true
        state: present

- name: Delete multiple container distributions
  stackhpc.pulp.container_distributions:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    distributions:
      - name: dist1
        state: absent
      - name: dist2
        state: absent
"""

RETURN = r"""
  distributions:
    description: List of container distribution results
    type: list
    returned: always
    elements: dict
    contains:
      name:
        description: Name of the distribution
        type: str
      distribution:
        description: Distribution details (when applicable)
        type: dict
      changed:
        description: Whether the distribution was changed
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
    from pulp_glue.container.context import (
        PulpContainerDistributionContext,
        PulpContainerRepositoryContext,
    )
    from pulp_glue.common.context import PulpContext
    from pulp_glue.common.openapi import BasicAuthProvider
    from pulp_glue.common import __version__ as pulp_glue_version

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpContainerDistributionContext = None
    PulpContext = None
    BasicAuthProvider = None
    pulp_glue_version = None


class PulpBatchDistributionAnsibleModule(PulpAnsibleModule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process_single_distribution(self, entity):
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

            context = PulpContainerDistributionContext(pulp_ctx)
            natural_key = {"name": entity["name"]}
            desired_attributes = {}

            # Map fields
            if "base_path" in entity and entity["base_path"] is not None:
                desired_attributes["base_path"] = entity["base_path"]
            if "private" in entity and entity["private"] is not None:
                desired_attributes["private"] = entity["private"]
            if "content_guard" in entity and entity["content_guard"] is not None:
                desired_attributes["content_guard"] = entity["content_guard"]

            if "repository" in entity and entity["repository"]:
                repo_ctx = PulpContainerRepositoryContext(pulp_ctx, entity={"name": entity["repository"]})
                if not repo_ctx.entity:
                    result["failed"] = True
                    result["msg"] = f"Repository '{entity['repository']}' not found."
                    return result
                if "version" in entity and entity["version"] is not None:
                    repo_version = repo_ctx.get_version_context().find(number=entity["version"])
                    if repo_version:
                        desired_attributes["repository_version"] = repo_version["pulp_href"]
                    else:
                        result["failed"] = True
                        result["msg"] = f"Repository version '{entity['version']}' not found for repository '{entity['repository']}'."
                        return result
                else:
                    desired_attributes["repository"] = repo_ctx.entity["pulp_href"]

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
                result["distribution"] = after
        except Exception as e:
            result["failed"] = True
            result["msg"] = str(e)
        return result

    def process_batch_distributions(self, distributions, concurrency=10):
        results = []
        overall_changed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self.process_single_distribution, entity) for entity in distributions]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result["changed"]:
                    overall_changed = True
                results.append(result)

        # Sort results by original order
        results.sort(key=lambda x, m={e["name"]: i for i, e in enumerate(distributions)}: m[x["name"]])

        if overall_changed:
            self.set_changed()
        self.set_result("distributions", results)
        if any(r["failed"] for r in results):
            self.fail_json(msg="One or more items failed", distributions=results)


def main():
    with PulpBatchDistributionAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "distributions": {
                "type": "list",
                "elements": "dict",
                "options": {
                    "name": {"required": True, "type": "str"},
                    "base_path": {"type": "str"},
                    "repository": {"type": "str"},
                    "version": {"type": "int"},
                    "content_guard": {"type": "str"},
                    "private": {"type": "bool"},
                    "state": {"choices": ["present", "absent"], "default": "present", "type": "str"},
                },
                "required": True,
            },
            "concurrency": {"type": "int", "default": 10},
        },
    ) as module:
        module.process_batch_distributions(module.params["distributions"], module.params["concurrency"])


if __name__ == "__main__":
    main()
