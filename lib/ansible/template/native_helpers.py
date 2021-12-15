# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import ast
from itertools import islice, chain

from jinja2.runtime import StrictUndefined

from ansible.module_utils._text import to_text
from ansible.module_utils.common.collections import is_sequence, Mapping
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.native_jinja import NativeJinjaText
from ansible.utils.unsafe_proxy import wrap_var


_JSON_MAP = {
    "true": True,
    "false": False,
    "null": None,
}


class Json2Python(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id not in _JSON_MAP:
            return node
        return ast.Constant(value=_JSON_MAP[node.id])


def _fail_on_undefined(data):
    """Recursively find an undefined value in a nested data structure
    and properly raise the undefined exception.
    """
    if isinstance(data, Mapping):
        for value in data.values():
            _fail_on_undefined(value)
    elif is_sequence(data):
        for item in data:
            _fail_on_undefined(item)
    else:
        if isinstance(data, StrictUndefined):
            # To actually raise the undefined exception we need to
            # access the undefined object otherwise the exception would
            # be raised on the next access which might not be properly
            # handled.
            # See https://github.com/ansible/ansible/issues/52158
            # and StrictUndefined implementation in upstream Jinja2.
            str(data)

    return data


def ansible_concat(nodes, convert_data, variable_start_string):
    head = list(islice(nodes, 2))

    if not head:
        return None

    if len(head) == 1:
        out = _fail_on_undefined(head[0])

        if isinstance(out, NativeJinjaText):
            return out

        out = to_text(out)
    else:
        out = ''.join([to_text(_fail_on_undefined(v)) for v in chain(head, nodes)])

    if not convert_data:
        return out

    # if this looks like a dictionary, list or bool, convert it to such
    do_eval = (
        (
            out.startswith(('{', '[')) and
            not out.startswith(variable_start_string)
        ) or
        out in ('True', 'False')
    )
    if do_eval:
        unsafe = hasattr(out, '__UNSAFE__')
        try:
            out = ast.literal_eval(
                ast.fix_missing_locations(
                    Json2Python().visit(
                        ast.parse(out, mode='eval')
                    )
                )
            )
        except (ValueError, SyntaxError, MemoryError):
            pass
        else:
            if unsafe:
                out = wrap_var(out)

    return out


def ansible_native_concat(nodes):
    """Return a native Python type from the list of compiled nodes. If the
    result is a single node, its value is returned. Otherwise, the nodes are
    concatenated as strings. If the result can be parsed with
    :func:`ast.literal_eval`, the parsed value is returned. Otherwise, the
    string is returned.

    https://github.com/pallets/jinja/blob/master/src/jinja2/nativetypes.py
    """
    head = list(islice(nodes, 2))

    if not head:
        return None

    if len(head) == 1:
        out = _fail_on_undefined(head[0])

        # TODO send unvaulted data to literal_eval?
        if isinstance(out, AnsibleVaultEncryptedUnicode):
            return out.data

        if isinstance(out, NativeJinjaText):
            # Sometimes (e.g. ``| string``) we need to mark variables
            # in a special way so that they remain strings and are not
            # passed into literal_eval.
            # See:
            # https://github.com/ansible/ansible/issues/70831
            # https://github.com/pallets/jinja/issues/1200
            # https://github.com/ansible/ansible/issues/70831#issuecomment-664190894
            return out

        # short-circuit literal_eval for anything other than strings
        if not isinstance(out, string_types):
            return out
    else:
        out = ''.join([to_text(_fail_on_undefined(v)) for v in chain(head, nodes)])

    try:
        return ast.literal_eval(
            # In Python 3.10+ ast.literal_eval removes leading spaces/tabs
            # from the given string. For backwards compatibility we need to
            # parse the string ourselves without removing leading spaces/tabs.
            ast.parse(out, mode='eval')
        )
    except (ValueError, SyntaxError, MemoryError):
        return out
