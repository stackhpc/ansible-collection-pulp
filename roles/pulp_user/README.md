pulp_user
================

This role creates and deletes Pulp users using the Pulp API.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_admin_username`: Username used to access Pulp server. Default is `admin`
* `pulp_admin_password`: Password used to access Pulp server. Default is unset
* `pulp_users`: List of users to create/update/delete. Default is an empty list. Each item is a dict containing:
  * `username` (Required)
  * `password`
  * `first_name` 
  * `last_name` 
  * `email`
  * `is_staff`
  * `is_active`
  * `state` (default is `present`. Setting this value to `absent` will delete the use if it exists)
  * `groups` (list of groups to add the user to) 

Note: User groups are evaluated against the user's current list of groups returned from the Pulp server API. Removing a group from the list of groups defined in `pulp_users[*].groups` will result in the user being removed from that group, and adding a group will result in the user being added to that group. Adding an empty `groups:` for a user will result in that user being removed from all groups.

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
      pulp_users:
        - username: example-user-1
          password: correct horse battery staple
          groups:
            - existing.container.namespace.consumers.one
            - existing.container.namespace.consumers.two
          state: present
        - username: example-user-2
          groups:
            - existing.container.namespace.consumers.one
          state: present
        - username: example-user-3
          state: absent
```
