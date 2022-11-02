pulp_group
================

This role creates and deletes Pulp groups using the Pulp API. 

To add users to groups or add groups to content guards, use the pulp_user and pulp_content_guard_rbac roles respectively.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_admin_username`: Username used to access Pulp server. Default is `admin`
* `pulp_admin_password`: Password used to access Pulp server. Default is unset
* `pulp_groups_present`: List of groups to be present. Default is an empty list.
* `pulp_groups_absent`: List of groups to be absent. Default is an empty list.



Example playbook
----------------

```
---
- name: Create and delete groups
  gather_facts: True
  hosts: localhost
  roles:
    - role: stackhpc.pulp.pulp_group
      pulp_url: https://pulp.example.com
      pulp_admin_username: admin
      pulp_admin_password: "{{ secrets_pulp_admin_password }}"
      pulp_groups_present:
        - example-group-1
        - example-group-2
      pulp_groups_absent:
        - example-group-3
```
