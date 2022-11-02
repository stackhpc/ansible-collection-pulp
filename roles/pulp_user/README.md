pulp_user
================

This role creates and deletes Pulp users using the Pulp API.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_admin_username`: Username used to access Pulp server. Default is `admin`
* `pulp_admin_password`: Password used to access Pulp server. Default is unset
* `pulp_users_present`: List of users to be present. Default is an empty list.
* `pulp_users_absent`: List of users to be absent. Default is an empty list.

Note: User groups are evaluated against the user's current list of groups returned from the Pulp server API. Removing a group from the list of groups defined in `pulp_users_present[*].groups` will result in the user being removed from that group, and adding a group will result in the user being added to that group. Adding an empty `groups:` for a user will result in that user being removed from all groups.

Example playbook
----------------

```
---
- name: Create and delete users
  gather_facts: True
  hosts: localhost
  roles:
    - role: stackhpc.pulp.pulp_user
      pulp_url: https://pulp.example.com
      pulp_admin_username: admin
      pulp_admin_password: "{{ secrets_pulp_admin_password }}"
      pulp_users_present:
        - username: example-user-1
          password: correct horse battery staple
          groups:
            - existing.container.namespace.consumers.one
            - existing.container.namespace.consumers.two
        - username: example-user-2
          password: germany ansible rain farmer
          groups:
            - existing.container.namespace.consumers.one
      pulp_users_absent:
        - example-user-3
```
