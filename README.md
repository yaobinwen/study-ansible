# Study Notes

## 1. Overview

This document has my study notes of Ansible and also serves as a quick guide for me to recall how to use Ansible for various purposes. The original README is [here](./README.rst).

In order to help understand the code, I added comments or debugging log messages which all have the tag `[ywen]`.

I created a branch `ywen/v2.9.12` to study the code of the version `2.9.12`. As of 2021-12-14, I haven't studied the code of any other versions.

## 2. Develop and Debug Ansible

The latest version (i.e., the `devel` version) of the developer guide is here: [Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html). Note that Ansible may re-organize their documentation site so the links may become inaccessible. Should this happen, search the key word "Ansible Developer Guide".

This section uses the following references:
- [2.1] [Developing Ansible modules](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html)
  - [2.1.1] [Preparing an environment for developing Ansible modules](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html#preparing-an-environment-for-developing-ansible-modules)
  - [2.1.2] [Creating an info or a facts module](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html#creating-an-info-or-a-facts-module)
  - [2.1.3] [Creating a module](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html#creating-a-module)

### 2.1 Prepare Development Environment to Develop a Module

The development environment preparation is part of a larger scenario: Developing Ansible modules [2.1].

To prepare the development environment, refer to [2.1.1]. The main steps are as follows (assuming Ubuntu):

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

### 2.2 Decide Module Type

The document [2.1] mentions three types of modules:

| Type | Filename | Description | Template |
|:----:|:--------:|:------------|:--------:|
| info | `*_info.py` | Gathers information on other objects or files. | [2.1.2] |
| facts | `*_facts.py` | Gather information about the target machines. | [2.1.2] |
| general-purpose | `*.py` | For other purposes other than information or facts gathering. | [2.1.3] |

### 2.3 Testing the Module

[2.1] also talks about how to test the newly created module, such as sanity test and unit test.

As a note says:

> Ansible uses `pytest` for unit testing.

Usually, one cannot test the `run_module()` function directly because it requires two things:
- `stdin` as `AnsibleModule` reads its input arguments from the standard input.
- `exit_json()` and `fail_json()` call `sys.exit()` which will cause the test program to exit.

Therefore, usually one can only test the functions that the Ansible module calls. But the [`patch_ansible_module()` function](https://github.com/yaobinwen/ansible/blob/devel/test/units/modules/conftest.py#L16-L31) makes it possible to test the Ansible module directly:

```python
@pytest.fixture
def patch_ansible_module(request, mocker):
    if isinstance(request.param, string_types):
        args = request.param
    elif isinstance(request.param, MutableMapping):
        if 'ANSIBLE_MODULE_ARGS' not in request.param:
            request.param = {'ANSIBLE_MODULE_ARGS': request.param}
        if '_ansible_remote_tmp' not in request.param['ANSIBLE_MODULE_ARGS']:
            request.param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
        if '_ansible_keep_remote_files' not in request.param['ANSIBLE_MODULE_ARGS']:
            request.param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False
        args = json.dumps(request.param)
    else:
        raise Exception('Malformed data to the patch_ansible_module pytest fixture')

    mocker.patch('ansible.module_utils.basic._ANSIBLE_ARGS', to_bytes(args))
```

Currently (as of 2022-01-09), the only tests that use `patch_ansible_module()` is [`test_pip.py`](https://github.com/yaobinwen/ansible/blob/devel/test/units/modules/test_pip.py).

### 2.4 Display Messages

Use the module `lib/ansible/utils/display.py`. Search the code `from ansible.utils.display import Display` or something similar to find the examples in the codebase.

### 2.5 Debug Output vs `debug` Module Output

The "debug output" can refer to two things in Ansible, so be specific when talking about "debug output".

The first one is the log messages that are printed out by [`Display.debug()` method](lib/ansible/utils/display.py):

```python
class Display(metaclass=Singleton):

    # ...

    def debug(self, msg, host=None):
        if C.DEFAULT_DEBUG:
            if host is None:
                self.display("%6d %0.5f: %s" % (os.getpid(), time.time(), msg), color=C.COLOR_DEBUG)
            else:
                self.display("%6d %0.5f [%s]: %s" % (os.getpid(), time.time(), host, msg), color=C.COLOR_DEBUG)
```

These debugging log messages can be toggled by the [environment variable `ANSIBLE_DEBUG`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#envvar-ANSIBLE_DEBUG) and the color can be configured by [`ANSIBLE_COLOR_DEBUG`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#envvar-ANSIBLE_COLOR_DEBUG). For example:

```
ywen@ywen-Precision-7510:~$ export ANSIBLE_COLOR_DEBUG="bright yellow"
ywen@ywen-Precision-7510:~$ export ANSIBLE_DEBUG=1
ywen@ywen-Precision-7510:~$ ansible -m ping localhost
```

The second one is the output of the [`ansible.builtin.debug` module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/debug_module.html).

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

## 4. Modules and Files

This section is based on the version `2.9.12`. Check out the branch `ywen/v2.9.12`.

The `bin/ansible` is a symbolic link pointing at `lib/ansible/cli/scripts/ansible_cli_stub.py` which is the entry point of all the CLI execution. For example, running `ansible-playbook` will eventually run into the main module of `ansible_cli_stub.py`.

`lib/ansible/cli` has multiple modules:
- `adhoc.py`: For arbitrary Ansible module execution (e.g., `ansible -m`).
- `config.py`: For the CLI `ansible-config`.
- `console.py`: For the CLI `ansible-console`.
- `doc.py`: For the CLI `ansible-doc`.
- `galaxy.py`: For the CLI `ansible-galaxy`.
- `inventory.py`: For the CLI `ansible-inventory`.
- `playbook.py`: For the CLI `ansible-playbook`.
- `pull.py`: For the CLI `ansible-pull`.
- `vault.py`: For the CLI `ansible-vault`.

The class `PlaybookCLI` (`lib/ansible/cli/playbook.py`) is the CLI for running `ansible-playbook`. Look at its `run` method which uses the class `PlaybookExecutor` (`lib/ansible/executor/playbook_executor.py`) to run the playbook. Look at its `run` method.

`PlaybookExecutor` uses a `TaskQueueManager` (`lib/ansible/executor/task_queue_manager.py`) to run the tasks. Look at its `run` method.

Note that `TaskQueueManager` actually uses the _strategy_ to run the tasks:

```python
        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(new_play.strategy, self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

        # ...

        # and run the play using the strategy and cleanup on way out
        display.debug("[ywen] Run the play using the strategy {s}".format(s=strategy))
        play_return = strategy.run(iterator, play_context)
```

## 5. How to Display Role Path

When we debug a playbook, sometimes we want to figure out the actual path of the role in the playbook. As of `v2.9.12`, there doesn't seem to be a CLI option of `ansible` or `ansible-playbook` to show the role paths. But there are two other methods to do it.

The first method uses the debug output: Run [`export ANSIBLE_DEBUG=1`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#envvar-ANSIBLE_DEBUG) to enable debugging output. Then look for the debug log messages **"Loading data from"**:

```
 15267 1639582174.41790: Loading data from /home/ywen/wc/stable/minevisionsystems/hecla/ansible/roles/spinnaker/defaults/main.yml
 15267 1639582174.41857: Loading data from /home/ywen/wc/stable/minevisionsystems/hecla/ansible/roles/spinnaker/tasks/main.yml
```

The second method is to hack the code (assuming `v2.9.27`):
- `sudo vim /usr/lib/python2.7/dist-packages/ansible/playbook/role/definition.py`
- Find the following block (which should be line 90 ~ 94):

```python
        # first we pull the role name out of the data structure,
        # and then use that to determine the role path (which may
        # result in a new role name, if it was a file path)
        role_name = self._load_role_name(ds)
        (role_name, role_path) = self._load_role_path(role_name)
```

- Add a line of `display.v(...` right below the `_load_role_path` line:

```python
        (role_name, role_path) = self._load_role_path(role_name)
        display.v("Found role '{n}' at '{p}'".format(n=role_name, p=role_path))
```

- Running `ansible-playbook -v` (or any verbosity higher than `-v`) will print the used role path:

```
TASK [Spinnaker SDK requires preseeding debconf(1) to avoid interactive prompts while installing.] *********************************************************************************************************
Found role 'spinnaker' at '/home/ywen/wc/stable/minevisionsystems/hecla/ansible/roles/spinnaker'
```
