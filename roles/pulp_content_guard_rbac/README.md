pulp_content_guard_rbac
================

This role creates and deletes Pulp RBAC content guards using the Pulp API

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_admin_username`: Username used to access Pulp server. Default is `admin`
* `pulp_admin_password`: Password used to access Pulp server. Default is unset
* `pulp_content_guards_rbac_present`: List of groups to be present. Default is an empty list.
* `pulp_content_guards_rbac_absent`: List of groups to be absent. Default is an empty list.

Note: The groups associated with specified content guards are evauluated against the user's current list of content guards, and their respective groups, returned from the Pulp server API. Removing a group from the list of groups defined in `pulp_content_guards_rbac_present[*].download_groups` will result in the group being removed from that content guard, and adding a group will result in the group being added to that content guard. Adding an empty `download_groups:` for a content guard will result in all groups being removed for that content guard.

Example playbook
----------------

```
---
- name: Create and delete Pulp RBAC content guards
  gather_facts: True
  hosts: localhost
  roles:
    - role: stackhpc.pulp.pulp_content_guard_rbac
      pulp_url: https://pulp.example.com
      pulp_admin_username: admin
      pulp_admin_password: "{{ secrets_pulp_admin_password }}"
      pulp_content_guards_rbac_present:
        - name: content-guard-1
          download_groups:
            - existing-group-1
            - existing-group-2
        - name: content-guard-2
          download_groups:
            - existing-group-3
      pulp_content_guards_rbac_absent:
        - content-guard-3
        - content-guard-4
```
