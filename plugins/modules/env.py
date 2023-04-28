#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2023, Pedro Tôrres <t0rr3sp3dr0@gmail.com>
# Apache License 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
module: env
description: >
  The install operation creates a new user environment, based on the current
  generation of the active profile, to which a set of store paths described by
  args is added.
short_description: nix-env -f ./defexpr.nix -ir
version_added: 0.0.1
author:
  - Pedro Tôrres (@t0rr3sp3dr0)
extends_documentation_fragment:
  - community.general.attributes
options:
  derivations:
    description: List of packages by channel.
    required: true
    type: dict[str,list[str]]
'''


EXAMPLES = r'''
- name: nix_env
  t0rr3sp3dr0.nix.env:
    derivations:
      nixpkgs:
        - bash
        - git
      nixpkgs-unstable:
        - python
'''


RETURN = r'''
#
'''


import textwrap
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.validation import (check_type_dict, check_type_list, check_type_str)


class NixEnv:
    def __init__(self):
        self.module = AnsibleModule(
            argument_spec={
                'derivations': {
                    'type': NixEnv.__check_type_derivations,
                    'required': True,
                },
            },
            supports_check_mode=True,
        )

        self.result = {
            'changed': False
        }

    @staticmethod
    def __check_type_derivations(derivations):
        derivations = check_type_dict(derivations)
        for channel, names in derivations.items():
            channel = check_type_str(channel)
            names = check_type_list(names)
            for name in names:
                name = check_type_str(name)
        return derivations

    def make_defexpr(self):
        DEFEXPR_NIX = textwrap.dedent('''\
            let
              {lblock}
            in {{
              {iblock}
            }}
        ''')

        lblock = []
        iblock = []

        derivations = self.module.params['derivations']
        for channel, packages in derivations.items():
            lexpr = '{channel} = import <{channel}> {{}};'.format(channel=channel)
            lblock.append(lexpr)
            iexpr = 'inherit ({channel}) {packages};'.format(channel=channel, packages=' '.join(packages))
            iblock.append(iexpr)

        content = DEFEXPR_NIX.format(lblock='\n  '.join(lblock), iblock='\n  '.join(iblock))
        content = content.encode('utf-8')

        try:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(content)
                return f.name
        except Exception as e:
            msg = str(e)
            self.module.fail_json(msg)

    def run_install(self, defexpr_path):
        bin_path = self.module.get_bin_path('nix-env', required=True, opt_dirs=['/nix/var/nix/profiles/default/bin'])
        dry_run = ('--dry-run') if self.module.check_mode else ()

        argv = [bin_path, *dry_run, '-f', defexpr_path, '-ir']
        _, stdout, stderr = self.module.run_command(argv, check_rc=True)
        self.module.debug(stdout)
        self.module.debug(stderr)

        if not dry_run:
            self.result['changed'] = True

    def run(self):
        defexpr_path = self.make_defexpr()
        self.run_install(defexpr_path)
        self.module.exit_json(**self.result)


def main():
    nix_env = NixEnv()
    nix_env.run()


if __name__ == '__main__':
    main()
