pulp_repository
=======

This role configures and synchronizes Pulp server repositories.

Role variables
--------------

* `pulp_url`: URL of Pulp server
* `pulp_username`: Username used to access Pulp server
* `pulp_password`: Password used to access Pulp server
* `pulp_validate_certs`: Whether to validate Pulp server certificate
* `pulp_publication_rpm`: List of RPM repositories
* `pulp_publication_python`: List of PyPI repositories
* `pulp_publication_deb`: List of Deb respositories

Example playbook
----------------

```
---
- name: Run pulp roles
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_publication
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_publication_rpm:
        - repository: centos-baseos
          version: 14
          state: present
        - repository: centos-appstream
          version: 14
          state: present
      pulp_publication_deb:
        - repository: ubuntu
          version: 13
          state: present
```
