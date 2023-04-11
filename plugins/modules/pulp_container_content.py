#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: pulp_container_content
short_description: Manage container content of a pulp api server instance
description:
  - "This performs CRUD operations on container content in a pulp api server instance."
options:
  allow_missing:
    description:
      - Whether to allow missing tags when state is present.
    type: bool
    default: false
  src_repo:
    description:
      - Name of the repository to copy content from when state is present.
    type: str
  src_is_push:
    description:
      - Whether src_repo is a container-push repository.
    type: bool
    default: false
  repository:
    description:
      - Name of the repository to add or remove content
    type: str
    required: true
  tags:
    description:
      - List of tags to add or remove
    type: list
    items: str
    required: true
extends_documentation_fragment:
  - pulp.squeezer.pulp
  - pulp.squeezer.pulp.entity_state
author:
  - Mark Goddard (@markgoddard)
"""

EXAMPLES = r"""
- name: Copy tag1 and tag2 from repo1 to repo2
  pulp_container_content:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: repo2
    src_repo: repo1
    tags:
      - tag1
      - tag2

- name: Remove tag3 from repo3
  pulp_container_content:
    pulp_url: https://pulp.example.org
    username: admin
    password: password
    repository: repo3
    tags:
      - tag3
    state: absent
"""

RETURN = r"""
  repository_version:
    description: Created container repository version
    type: dict
    returned: when content is added or removed
"""


from ansible_collections.pulp.squeezer.plugins.module_utils.pulp import (
    PAGE_LIMIT,
    PulpContainerRepository,
    PulpEntity,
    PulpEntityAnsibleModule,
    PulpTask,
    SqueezerException,
)


class PulpContainerRepositoryContent(PulpContainerRepository):
    _add_id = "repositories_container_container_add"
    _remove_id = "repositories_container_container_remove"
    _container_tags_list_id = "content_container_tags_list"

    _name_singular = "repository_version"

    def get_src_repo(self):
        # Query source repository.
        natural_key = {"name": self.module.params["src_repo"]}
        repo = PulpContainerRepository(self.module, natural_key)
        if self.module.params["state"] == "present" and self.module.params["src_is_push"]:
            repo._list_id = "repositories_container_container_push_list"
        # find populates repo.entity.
        repo.find(failsafe=False)
        return repo

    def get_content_units(self, repo):
        # Query container tags with matching names in repo.
        # Pagination code adapted from PulpEntity.list().
        tags = []
        offset = 0
        search_result = {"next": True}
        while search_result["next"]:
            parameters = {
                "limit": PAGE_LIMIT,
                "offset": offset,
                "name__in": ",".join(self.module.params["tags"]),
                "repository_version": repo.entity["latest_version_href"]
            }
            search_result = self.module.pulp_api.call(
                self._container_tags_list_id, parameters=parameters
            )
            tags.extend(search_result["results"])
            offset += PAGE_LIMIT

        if (self.module.params["state"] == "present" and
            not self.module.params["allow_missing"] and
            len(tags) != len(self.module.params["tags"])):
            missing = ", ".join(set(self.module.params["tags"]) - set(tags))
            raise SqueezerException(f"Some tags not found in source repository: {missing}")
        return [result["pulp_href"] for result in tags]

    def add_or_remove(self, add_or_remove_id, content_units):
        body = {"content_units": content_units}
        if not self.module.check_mode:
            parameters = {"container_container_repository_href": self.entity["pulp_href"]}
            response = self.module.pulp_api.call(
                add_or_remove_id, body=body, uploads=self.uploads, parameters=parameters
            )
            if response and "task" in response:
                task = PulpTask(self.module, {"pulp_href": response["task"]}).wait_for()
                # Adding or removing content results in creation of a new repository version
                if task["created_resources"]:
                    self.entity = {"pulp_href": task["created_resources"][0]}
                    self.module.set_changed()
                else:
                    self.entity = None
            else:
                self.entity = response
        else:
            # Assume changed in check mode
            self.module.set_changed()

    def add(self):
        src_repo = self.get_src_repo()
        self.add_or_remove(self._add_id, self.get_content_units(src_repo))

    def remove(self):
        self.add_or_remove(self._remove_id, self.get_content_units(self))

    def process(self):
        # Populate self.entity.
        self.find(failsafe=False)
        if self.module.params["state"] == "present":
            response = self.add()
        elif self.module.params["state"] == "absent":
            response = self.remove()
        else:
            raise SqueezerException("Unexpected state")
        self.module.set_result(self._name_singular, self.presentation(self.entity))


def main():
    with PulpEntityAnsibleModule(
        argument_spec=dict(
            allow_missing={"type": "bool", "default": False},
            repository={"required": True},
            src_repo={},
            src_is_push={"type": "bool", "default": False},
            state={"default": "present"},
            tags={"type": "list", "item": "str", "required": True},
        ),
        required_if=[("state", "present", ["src_repo"])],
    ) as module:
        natural_key = {"name": module.params["repository"]}
        PulpContainerRepositoryContent(module, natural_key).process()


if __name__ == "__main__":
    main()
