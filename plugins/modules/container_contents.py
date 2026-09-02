#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, StackHPC
# Apache License, Version 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

DOCUMENTATION = r"""
---
module: container_contents
short_description: Manage content of multiple container repositories of a pulp api server instance
description:
  - "This adds or removes tags in multiple container repositories in a pulp api server
     instance in a single call, processing items concurrently."
options:
  contents:
    description:
      - List of content operations to perform
    type: list
    elements: dict
    required: true
    suboptions:
      repository:
        description:
          - Name of the repository to copy to when state is present, or the
            repository to remove from when state is absent
        type: str
        required: true
      is_push:
        description:
          - Whether the destination repository is a container-push repository
        type: bool
        default: false
      src_repo:
        description:
          - Name of the repository to copy from when state is present
        type: str
      src_is_push:
        description:
          - Whether the source repository is a container-push repository
        type: bool
        default: false
      tags:
        description:
          - List of names of tags to add or remove
        type: list
        elements: str
        required: true
      allow_missing:
        description:
          - Whether to ignore tags missing from the source repository
        type: bool
        default: false
      state:
        description:
          - Whether to add or remove content, or only check that the tags exist
        type: str
        choices: ["present", "absent", "read"]
        default: present
  concurrency:
    description:
      - Maximum number of concurrent operations
    type: int
    default: 10
  wait:
    description:
      - Whether to wait for content addition and removal tasks to complete
    type: bool
    default: true
extends_documentation_fragment:
  - pulp.squeezer.pulp
author:
  - Alex Welsh (@alex-welsh)
"""

EXAMPLES = r"""
- name: Promote images from the dev namespace to the release namespace
  stackhpc.pulp.container_contents:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    contents:
      - src_repo: stackhpc-dev/nova-compute
        src_is_push: true
        repository: stackhpc/nova-compute
        tags:
          - 2026.1-rocky-10
      - src_repo: stackhpc-dev/neutron-server
        src_is_push: true
        repository: stackhpc/neutron-server
        tags:
          - 2026.1-rocky-10
  register: content_results

- name: Remove tags from repositories with custom concurrency
  stackhpc.pulp.container_contents:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    concurrency: 5
    contents:
      - repository: stackhpc/nova-compute
        tags:
          - 2025.1-rocky-9
        state: absent
"""

RETURN = r"""
  contents:
    description: List of content operation results, in the order supplied
    type: list
    returned: always
    elements: dict
    contains:
      repository:
        description: Name of the destination repository
        type: str
      changed:
        description: Whether content was added to or removed from the repository
        type: bool
      failed:
        description: Whether the operation failed
        type: bool
      msg:
        description: Error message if failed
        type: str
      missing_tags:
        description: Tags not found in the reference repository
        type: list
      task:
        description: Href of the dispatched task, when content was submitted
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
    from pulp_glue.common.context import PulpContext
    from pulp_glue.common.openapi import BasicAuthProvider
    from pulp_glue.common import __version__ as pulp_glue_version

    PULP_GLUE_IMPORT_ERR = None
except ImportError:
    PULP_GLUE_IMPORT_ERR = traceback.format_exc()
    PulpContext = None
    BasicAuthProvider = None
    pulp_glue_version = None


class ContentError(Exception):
    """An expected error, reportable without a traceback."""


REPO_LIST_OP = "repositories_container_container_list"
PUSH_REPO_LIST_OP = "repositories_container_container_push_list"
TAG_LIST_OP = "content_container_tags_list"
ADD_OP = "repositories_container_container_add"
REMOVE_OP = "repositories_container_container_remove"


class PulpBatchContentAnsibleModule(PulpAnsibleModule):
    def _pulp_ctx(self):
        # Create a separate PulpContext for each thread to avoid correlation ID conflicts
        auth_args = {}
        if self.params["username"]:
            auth_args["auth_provider"] = BasicAuthProvider(
                username=self.params["username"],
                password=self.params["password"],
            )

        return PulpContext(
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

    @staticmethod
    def _find_repo(pulp_ctx, name, is_push):
        operation_id = PUSH_REPO_LIST_OP if is_push else REPO_LIST_OP
        response = pulp_ctx.call(operation_id, parameters={"name": name})
        if response["count"] == 0:
            return None
        return response["results"][0]

    def process_single_content(self, content_item):
        result = {
            "repository": content_item["repository"],
            "changed": False,
            "failed": False,
            "msg": "",
        }
        try:
            pulp_ctx = self._pulp_ctx()
            state = content_item["state"]

            dest_repo = self._find_repo(
                pulp_ctx, content_item["repository"], content_item["is_push"]
            )
            if dest_repo is None:
                raise ContentError(
                    f"Destination repository '{content_item['repository']}' not found."
                )

            # For 'present', tags are resolved against the source repository. For
            # 'absent' and 'read' they are resolved against the destination.
            if state == "present":
                if content_item["src_repo"] is None:
                    raise ContentError(
                        "'src_repo' is required when state is 'present'."
                    )
                src_repo = self._find_repo(
                    pulp_ctx, content_item["src_repo"], content_item["src_is_push"]
                )
                if src_repo is None:
                    raise ContentError(
                        f"Source repository '{content_item['src_repo']}' not found."
                    )
                ref_repo_version = src_repo["latest_version_href"]
            else:
                ref_repo_version = dest_repo["latest_version_href"]

            tags = pulp_ctx.call(
                TAG_LIST_OP,
                parameters={
                    "name__in": content_item["tags"],
                    "repository_version": ref_repo_version,
                },
            )["results"]

            found_tags = [tag["name"] for tag in tags]
            missing_tags = [t for t in content_item["tags"] if t not in found_tags]
            # Missing tags are only an error when reading from a reference
            # repository. Removing a tag that is already absent is a no-op, so
            # that a second 'absent' run is idempotent.
            if (
                missing_tags
                and state in ("present", "read")
                and not content_item["allow_missing"]
            ):
                raise ContentError(
                    "Some tags not found in source repository: "
                    + ", ".join(missing_tags)
                )
            result["missing_tags"] = missing_tags

            content_units = [tag["pulp_href"] for tag in tags]
            if state == "read" or not content_units:
                return result

            if state == "present":
                # Only submit units the destination does not already serve, so
                # that re-promoting an unchanged tag is not reported as a change.
                existing = pulp_ctx.call(
                    TAG_LIST_OP,
                    parameters={
                        "name__in": content_item["tags"],
                        "repository_version": dest_repo["latest_version_href"],
                    },
                )["results"]
                existing_units = {tag["pulp_href"] for tag in existing}
                content_units = [
                    href for href in content_units if href not in existing_units
                ]
                if not content_units:
                    return result

            # Matches the previous implementation, which reported a change whenever
            # units were submitted rather than diffing the destination first.
            result["changed"] = True
            if self.check_mode:
                return result

            task = pulp_ctx.call(
                ADD_OP if state == "present" else REMOVE_OP,
                non_blocking=not self.params["wait"],
                parameters={
                    "container_container_repository_href": dest_repo["pulp_href"]
                },
                body={"content_units": content_units},
            )
            if isinstance(task, dict):
                result["task"] = task.get("pulp_href")
        except ContentError as exc:
            result["failed"] = True
            result["msg"] = str(exc)
        except Exception:
            result["failed"] = True
            result["msg"] = traceback.format_exc()
        return result

    def process_batch_contents(self, contents, concurrency=10):
        if concurrency < 1:
            self.fail_json(
                msg="concurrency must be at least 1, got {0}".format(concurrency)
            )
            return

        results = [None] * len(contents)
        overall_changed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(self.process_single_content, content_item): index
                for index, content_item in enumerate(contents)
            }
            for future in concurrent.futures.as_completed(futures):
                index = futures[future]
                result = future.result()
                if result["changed"]:
                    overall_changed = True
                results[index] = result

        if overall_changed:
            self.set_changed()
        self.set_result("contents", results)
        failures = [r for r in results if r["failed"]]
        if failures:
            detail = "; ".join(
                "{0}: {1}".format(r["repository"], r["msg"].strip().splitlines()[-1])
                for r in failures
            )
            self.fail_json(
                msg="{0} of {1} content operations failed: {2}".format(
                    len(failures), len(results), detail
                ),
                contents=results,
            )


def main():
    with PulpBatchContentAnsibleModule(
        import_errors=[("pulp-glue", PULP_GLUE_IMPORT_ERR)],
        argument_spec={
            "contents": {
                "type": "list",
                "elements": "dict",
                "required": True,
                "options": {
                    "repository": {"required": True, "type": "str"},
                    "is_push": {"type": "bool", "default": False},
                    "src_repo": {"type": "str"},
                    "src_is_push": {"type": "bool", "default": False},
                    "tags": {"type": "list", "elements": "str", "required": True},
                    "allow_missing": {"type": "bool", "default": False},
                    "state": {
                        "choices": ["present", "absent", "read"],
                        "default": "present",
                    },
                },
            },
            "concurrency": {"type": "int", "default": 10},
            "wait": {"type": "bool", "default": True},
        },
    ) as module:
        module.process_batch_contents(
            module.params["contents"], module.params["concurrency"]
        )


if __name__ == "__main__":
    main()
