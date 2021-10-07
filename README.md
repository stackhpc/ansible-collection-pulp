# StackHPC pulp collection

[![Tests](https://github.com/stackhpc/ansible-collection-pulp/actions/workflows/pull_request.yml/badge.svg)](https://github.com/stackhpc/ansible-collection-pulp/actions/workflows/pull_request.yml) [![Publish to Galaxy](https://github.com/stackhpc/ansible-collection-pulp/actions/workflows/publish.yml/badge.svg)](https://github.com/stackhpc/ansible-collection-pulp/actions/workflows/publish.yml)

Test

This repo contains `stackhpc.pulp` Ansible Collection. The collection includes roles supported by StackHPC for Pulp repository server configuration.
Note: Pulp server installation is out of this collection's scope - for this purpose please see [an official collection](https://galaxy.ansible.com/pulp/pulp_installer).

## Tested with Ansible

Tested with the current Ansible 2.9-2.10 releases.

## Included content

pulp_repository role

## Using this collection

Before using the collection, you need to install the collection with the `ansible-galaxy` CLI:

    ansible-galaxy collection install stackhpc.pulp

You can also include it in a `requirements.yml` file and install it via ansible-galaxy collection install -r requirements.yml` using format:

```yaml
collections:
- name: stackhpc.pulp
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

Apache License Version 2.0
