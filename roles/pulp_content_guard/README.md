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
  * `state` (default is `present`. Setting this value to `absent` will delete the content guard if it exists)
* `pulp_content_guard_rbac`: List of groups to create/update/delete. Default is an empty list. Each item is a dict containing:
  * `name` (Required)
  * `download_groups` (list of groups to to be added to this content guard with the download role) 
  * `state` (default is `present`. Setting this value to `absent` will delete the content guard if it exists)


Example playbook
----------------

```
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
        - name: alex-test-rbac_cg-1
          description: test-description-edited
          download_groups:
            - alex-test-group-1
            - alex-test-group-2
          state: present
        - name: alex-test-rbac_cg-2
          description: test-description2-edited
          download_groups:
            - alex-test-group-2
        - name: alex-test-rbac_cg-3
          description: test-description3-edited
          download_groups:
            - alex-test-group-1
          state: absent
```
