# Ansible - oVirt

This library contains ansible scripts for automating oVirt/RHV tasks. These playbooks assume that the oVirt API credentials are stored in environment variables.

```bash
export OVIRT_URL="https://ovirt.example.com/ovirt-engine/api"
export OVIRT_USERNAME="user@login_domain"
export OVIRT_PASSWORD="password"
```

The ovirt4.py dynamic inventory file is included for convenience but is not guaranteed to be cannon. It can be used with playbooks like so:

```bash
export OVIRT_URL="https://ovirt.example.com/ovirt-engine/api"
export OVIRT_USERNAME="user@login_domain"
export OVIRT_PASSWORD="password"

ansible-playbook -i ovirt4.py -l test-0 remove_ovirt_vm.yml
```
