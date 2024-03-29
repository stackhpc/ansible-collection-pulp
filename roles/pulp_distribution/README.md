pulp_distribution
=================

This role configures Pulp server distributions.

Role variables
--------------

* `pulp_url`: URL of Pulp server. Default is `http://localhost:8080`
* `pulp_username`: Username used to access Pulp server. Default is `admin`
* `pulp_password`: Password used to access Pulp server. Default is unse
* `pulp_validate_certs`: Whether to validate Pulp server certificate. Default is `true`
* `pulp_distribution_container`: List of distributions for container repositories. Default is an empty list
* `pulp_distribution_deb`: List of distributions for Deb repositories. Default is an empty list
* `pulp_distribution_rpm`: List of distributions for RPM repositories. Default is an empty list
* `pulp_distribution_deb_skip_existing`: Whether to skip existing Deb
  distributions. If true, new distributions will not be created for a
  publication if any distributions exist for the same publication.
  Default is `false`.
* `pulp_distribution_rpm_skip_existing`: Whether to skip existing RPM
  distributions. If true, new distributions will not be created for a
  publication if any distributions exist for the same publication.
  Default is `false`.

Example playbook
----------------

```yaml
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
      pulp_distribution_container:
        # Distribute the latest version of the pulp/pulp repository.
        - name: pulp/pulp
          base_path: pulp/pulp
          repository: pulp/pulp
          state: present
        # Distribute version 2 of the pulp/pulp repository with a content guard.
        - name: pulp/pulp
          base_path: pulp/pulp
          repository: pulp/pulp
          version: 2
          content_guard: secure-content-guard
          state: present
      pulp_distribution_deb:
        # Distribute the latest version of the ubuntu-focal repository.
        - name: ubuntu-focal
          base_path: ubuntu-focal
          repository: ubuntu-focal
          state: present
        # Distribute version 2 of the ubuntu-focal-security repository.
        - name: ubuntu-focal-security
          base_path: ubuntu-focal-security
          repository: ubuntu-focal-security
          version: 2
          state: present
        # Distribute the same publication as the ubuntu-focal distribution with a content guard.
        - name: ubuntu-focal-production
          base_path: ubuntu-focal-production
          distribution: ubuntu-focal
          content_guard: secure-content-guard
          state: present
      pulp_distribution_rpm:
        # Distribute the latest version of the centos-baseos repository.
        - name: centos-baseos
          base_path: centos-baseos
          repository: centos-baseos
          state: present
        # Distribute version 2 of the centos-appstream repository.
        - name: centos-appstream
          base_path: centos-appstream
          repository: centos-appstream
          version: 2
          state: present
        # Distribute the same publication as the centos-baseos distribution with a content guard.
        - name: centos-baseos-production
          base_path: centos-baseos-production
          distribution: centos-baseos
          content_guard: secure-content-guard
          state: present
```
