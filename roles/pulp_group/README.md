pulp_group
================

This role creates and deletes Pulp groups using the Pulp API. 

To add users to groups or add groups to content guards, use the pulp_user and pulp_content_guard roles respectively.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unset
* `pulp_groups`: List of groups to be created/updated/deleted. Default is an empty list. Each item is a dict containing:
  * `name` (Required)
  * `state` (default is `present`. Setting this value to `absent` will delete the use if it exists)



Example playbook
----------------

```yaml
---
- name: Create and delete groups
  gather_facts: True
  hosts: localhost
  roles:
    - role: stackhpc.pulp.pulp_group
      pulp_url: https://pulp.example.com
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_groups:
        - name: example-group-1
          state: present
        - name: example-group-2
          state: present
        - name: example-group-3
          state: absent
```
