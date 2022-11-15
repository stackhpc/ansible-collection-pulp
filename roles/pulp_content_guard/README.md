pulp_content_guard
==================

This role manages Pulp content guards.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unset
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_content_guard_x509_cert_guards`: List of x509 cert guards to create/update/delete. Each item is
  a dict containing: 
  * `name` (Required)
  * `description`
  * `ca_certificate`
  * `state` (Default is `present`. Setting this value to `absent` will delete the content guard if it exists)
* `pulp_content_guard_rbac`: List of RBAC content guards to create/update/delete. Default is an empty list. Each item is a dict containing:
  * `name` (Required)
  * `roles` List of dict containing:
    * `role` (role name)
    * `groups` List of groups to be assigned the role
  * `state` (default is `present`. Setting this value to `absent` will delete the content guard if it exists)

Note: groups assigned roles are evaluated against the content guard's current list of roles returned from the Pulp server API. Removing a group from the list of groups defined under any role in `pulp_content_guard_rbac[*].roles` will result in the group being removed, and adding a group will result in it being added. Adding an empty `groups:` for a role will result in all groups being removed from that role.

Example playbook
----------------

```yaml
---
- name: Create Pulp content guards
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_content_guard
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_content_guard_x509_cert_guards:
        - name: test_cert_guard
          description: For testing
          ca_certificate: |-
            -----BEGIN CERTIFICATE-----
            ...
            -----END CERTIFICATE-----
          state: present
          
    - role: stackhpc.pulp.pulp_content_guard
      pulp_url: http://localhost:8080
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_content_guard_rbac:
        - name: test_rbac_cg_1
          description: test content guard number 1
          roles:
            - role: core.rbaccontentguard_downloader
              groups:
            - role: core.rbaccontentguard_viewer
          state: present
        - name: test_rbac_cg_2
          state: absent
        - name: test_rbac_cg_3
          description: test content guard number 3
          roles:
            - role: core.rbaccontentguard_viewer
              groups:
                - test_group_1
                - test_group_2
```
