pulp_repository
=======

This role configures and synchronizes Pulp server repositories.

Role variables
--------------

repositories_rpm:
  - name: centos-baseos
    url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=BaseOS&infra=stock
    policy: on_demand
    state: present
  - name: centos-appstream
    url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=AppStream&infra=stock
    policy: on_demand
    state: present
  - name: epel
    url: https://mirrors.fedoraproject.org/mirrorlist?repo=epel-8&arch=x86_64&infra=stock&content=centos
    policy: on_demand
    state: present
  - name: epel-modular
    url: https://mirrors.fedoraproject.org/mirrorlist?repo=epel-modular-8&arch=x86_64&infra=stock&content=centos
    policy: on_demand
    state: present

repositories_deb:
  - name: ubuntu
    url: http://archive.ubuntu.com/ubuntu
    distributions: focal
    components: "main restricted"
    architectures: amd64
    policy: on_demand
    state: present

Example playbook
----------------

---
- name: Run pulp roles
  any_errors_fatal: True
  gather_facts: True
  hosts: all
  roles:
    - role: stackhpc.pulp.pulp_repository
      pulp_username: admin
      pulp_password: "{{ secrets_pulp_admin_password }}"
      repositories_rpm:
        - name: centos-baseos
          url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=BaseOS&infra=stock
          policy: on_demand
          state: immediate
        - name: centos-appstream
          url: http://mirrorlist.centos.org/?release=8&arch=x86_64&repo=AppStream&infra=stock
          policy: on_demand
          state: immediate
