pulp_repository
=======

This role configures and synchronizes Pulp server repositories.

Role variables
--------------

* `pulp_url`: URL of Pulp server
* `pulp_username`: Username used to access Pulp server
* `pulp_password`: Password used to access Pulp server
* `pulp_validate_certs`: Whether to validate Pulp server certificate
* `pulp_sync_remotes`: Whether to sync remotes with repositories
* `pulp_distribute`: Whether to publish and distribute repositories
* `pulp_repository_rpm_repos`: List of RPM repositories
* `pulp_repository_python_repos`: List of PyPI repositories
* `pulp_repository_deb_repos`: List of Deb respositories

Example playbook
----------------

```
---
- name: Run pulp roles
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_repository
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_repository_rpm_repos:
        - name: centos-baseos
          base_path: centos/8/baseos
          url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=BaseOS&infra=stock
          policy: on_demand
          state: present
        - name: centos-appstream
          base_path: centos/8/appstream
          url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=AppStream&infra=stock
          policy: on_demand
          state: present
      pulp_repository_deb_repos:
        - name: ubuntu
          base_path: ubuntu/focal/main
          url: http://archive.ubuntu.com/ubuntu
          distributions: focal
          components: "main restricted"
          architectures: amd64
          policy: on_demand
          state: present
```
