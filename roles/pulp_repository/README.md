pulp_repository
=======

This role configures and synchronizes Pulp server repositories.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `https://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unset
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_repository_container_repos`: List of container repositories. Default is an empty list.
* `pulp_repository_rpm_repos`: List of RPM repositories. Default is an empty list.
* `pulp_repository_python_repos`: List of PyPI repositories. Default is an empty list.
* `pulp_repository_deb_repos`: List of Deb respositories. Default is an empty list.

Example playbook
----------------

```yaml
---
- name: Run pulp roles
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_repository
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      pulp_repository_container_repos:
        # Create a pulp/pulp repository and sync with Dockerhub.
        - name: pulp/pulp
          url: https://registry-1.docker.io
          policy: on_demand
          state: present
      pulp_repository_rpm_repos:
        - name: centos-baseos
          url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=BaseOS&infra=stock
          policy: on_demand
          state: present
        - name: centos-appstream
          url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=AppStream&infra=stock
          policy: on_demand
          state: present
      pulp_repository_deb_repos:
        - name: ubuntu
          url: http://archive.ubuntu.com/ubuntu
          distributions: focal
          components: "main restricted"
          architectures: amd64
          policy: on_demand
          state: present
```
