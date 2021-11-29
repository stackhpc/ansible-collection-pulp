pulp_django_user
================

This role creates Django users using the Django admin site.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_admin_username`: Username used to access Pulp server. Default is `admin`
* `pulp_admin_password`: Password used to access Pulp server. Default is unset
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_django_users`: List of Django users to create. Default is an empty list.

Note: User groups are evauluated against the user's current list of groups returned from the Pulp server API. Removing a group from the list of groups defined in `pulp_django_users[*].groups` will result in the user being removed from that group, and adding a group will result in the user being added to that group. Adding an empty `groups:` for a user will result in that user being removed from all groups.

Example playbook
----------------

```
---
- name: Create Pulp Django users
  gather_facts: True
  hosts: localhost
  roles:
    - role: stackhpc.pulp.pulp_django_user
      pulp_url: https://pulp.example.com
      pulp_admin_username: admin
      pulp_admin_password: "{{ secrets_pulp_admin_password }}"
      pulp_django_users:
        - username: test-user
          password: correct horse battery staple
          groups:
            - existing.container.namespace.consumers.one
            - existing.container.namespace.consumers.two
```
