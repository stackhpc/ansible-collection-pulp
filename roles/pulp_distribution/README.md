pulp_distribution
=================

This role configures Pulp server distributions.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `http://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unse
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_distribution_rpm`: List of distributions for RPM repositories. Default is an empty list

Example playbook
----------------

```
---
- name: Manage Pulp distributions
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_distribution
      pulp_url: "https://pulp.example.com"
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_distribution_rpm:
        - name: centos-baseos
          base_path: centos-baseos
          publication:
          state: present
        - name: centos-appstream
          base_path: centos-appstream
          publication:
          state: present
```
