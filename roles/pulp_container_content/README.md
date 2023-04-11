pulp_container_content
======================

This role adds and removes content in Pulp container repositories.

Currently only supports tags.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unset
* `pulp_validate_certs`: Whether to validate certificates. Default is `true`.
* `pulp_container_content`: List of content to add or remove. Each item is a dict with the following keys:

  * `allow_missing`: Whether to ignore missing tags in the source repository
    when `state` is `present`.
  * `repository`: Name of the repository to copy to when `state is `present`
    or the repository to remove from when `state` is `absent`.
  * `src_repo`: Name of the repository to copy from when `state` is `present`.
  * `src_is_push`: Whether `src_repo` is a push repository. Default is `false`.
  * `state`: Whether to add (`present`) or remove (`absent`) content.
  * `tags`: List of names of tags to add or remove.

Example playbook
----------------

```yaml
---
- name: Add or remove container content
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: pulp_container_content
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_container_content:
        # Copy tag1 and tag2 from repo1 to repo2
        - src_repo: repo1
          src_is_push: true
          repository: repo2
          tags:
            - tag1
            - tag2
        # Remove tag3 from repo3
        - repository: repo3
          tags:
            - tag3
          state: absent
```
