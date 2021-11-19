pulp_content_guard
==================

This role manages Pulp content guards.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unset
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_content_guard_x509_cert_guards`: List of x509 cert guards. Each item is
  a dict with the following keys: `name`, `description`, `ca_certificate`,
  `state`.


Example playbook
----------------

```
---
- name: Create Pulp content guards
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_contentguard
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
```
