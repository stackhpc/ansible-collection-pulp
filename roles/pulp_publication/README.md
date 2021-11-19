pulp_publication
================

This role configures Pulp server publications.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `http://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unset
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_publication_deb`: List of publications of Deb repositories. Default is an empty list
* `pulp_publication_rpm`: List of publications of RPM repositories. Default is an empty list

Example playbook
----------------

```
---
- name: Manage Pulp publications
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_publication
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_publication_deb:
        # Create a publication of the latest version.
        - repository: ubuntu-focal
          state: present
        # Create a publication of version 2 using structured mode.
        - repository: ubuntu-focal
          version: 2
          mode: structured
          state: present
      pulp_publication_rpm:
        # Create a publication of the latest version.
        - repository: centos-baseos
          state: present
        # Create a publication of version 2.
        - repository: centos-appstream
          version: 2
          state: present
```
