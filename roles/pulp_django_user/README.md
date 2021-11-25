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
            - container.namespace.consumers.one
            - container.namespace.consumers.two
```
