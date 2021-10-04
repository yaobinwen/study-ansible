# Study Notes

## 1. Overview

This document has my study notes of Ansible and also serves as a quick guide for me to recall how to use Ansible for various purposes. The original README is [here](./README.rst).

## 2. Develop and Debug Ansible

The latest version (i.e., the `devel` version) of the developer guide is here: [Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html). Note that Ansible may re-organize their documentation site so the links may become inaccessible. Should this happen, search the key word "Ansible Developer Guide".

### 2.1 Prepare Development Environment to Develop a Module

The development environment preparation is part of a larger scenario: [Developing Ansible modules](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html)

To prepare the development environment: [Preparing an environment for developing Ansible modules](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html#preparing-an-environment-for-developing-ansible-modules). The main steps are as follows (assuming Ubuntu):

- 1). Install prerequisites:
  - The Debian packages:
    - build-essential
    - libssl-dev
    - libffi-dev
    - python-dev
    - python3-dev
    - python3-venv

- 2). Clone the Ansible repository: `$ git clone https://github.com/ansible/ansible.git`
- 3). Change directory into the repository root dir: `$ cd ansible`
- 4). Create a virtual environment:
  - `$ python3 -m venv venv` (or for Python 2 `$ virtualenv venv`. Note, this requires you to install the `virtualenv` package: `$ pip install virtualenv`)
- 5). Activate the virtual environment: `$ . venv/bin/activate`
- 6). Install development requirements: `$ pip install -r requirements.txt`
  - Make sure to upgrade `pip`: `pip install --upgrade pip` because Ubuntu 18.04 provides `pip 9.0.1` which is too old.
  - May need to install `setuptools_rust` using the latest version of `pip`: `pip install setuptools_rust`.
- 7). Run the environment setup script for each new development shell process: `$ . hacking/env-setup`

After the initial setup above, every time you are ready to start developing Ansible you should be able to just run the following from the root of the Ansible repo: `$ . venv/bin/activate && . hacking/env-setup`.

### 2.2 Display Messages

Use the module `lib/ansible/utils/display.py`. Search the code `from ansible.utils.display import Display` or something similar to find the examples in the codebase.

## 3. Sample Outputs

`ansible_facts` has [facts about the remote system](https://docs.ansible.com/ansible/latest/user_guide/playbooks_vars_facts.html#ansible-facts):
- Run `ansible <hostname> -m ansible.builtin.setup` to print the _raw_ information gathered for the remote system.
  - **NOTE**: If nothing is printed, try in a different folder which doesn't have `ansible.cfg`. I haven't looked into why a local `ansible.cfg` may cause the module `setup` to print nothing but I ran into this today (2021-08-12).
  - The raw information can be accessed directly, e.g., `"{{ansible_system}}"`.
  - It can be accessed via the variable `ansible_facts`, too: `{{ansible_facts.system}}` which is equivalent to `"{{ansible_system}}"`.
- Run `ansible <hostname> -m ansible.builtin.setup -a "filter=ansible_local"` to print just the information of the specified part.
- Click [`ansible_facts_raw.json`](./examples/ansible_facts_raw.json) to see a sample (from running `ansible.builtin.setup`).

The [Ansible document "Special Variables"](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html) doesn't list the details of some of the special variables. Here are some concrete examples for reference:
- `hostvars`:
  - A dictionary/map with all the hosts in inventory and variables assigned to them.
  - [`hostvars.json`](./examples/hostvars.json)
- `groups`:
  - A dictionary/map with all the groups in inventory and each group has the list of hosts that belong to it.
  - [`groups.json`](./examples/groups.json)
- `group_names`:
  - List of groups the current host is part of.
  - [`group_names.json`](./examples/group_names.json)
- `inventory_hostname`:
  - The inventory name for the ‘current’ host being iterated over in the play.
  - [`inventory_hostname.json`](./examples/inventory_hostname.json)
