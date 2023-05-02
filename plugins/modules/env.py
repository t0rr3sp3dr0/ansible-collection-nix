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
short_description: manipulate or query Nix user environments
version_added: 0.0.2
author:
  - Pedro Tôrres (@t0rr3sp3dr0)
options:
  config:
    description: Channels config set.
    default: '{}'
    type: str
  packages:
    description: Package names by channel.
    required: true
    type: dict[str,list[str]]
'''


EXAMPLES = r'''
- name: nix_env
  t0rr3sp3dr0.nix.env:
    config: |
      {
        allowUnfree = true;
      }
    packages:
      nixpkgs:
        - hello
      t0rr3sp3dr0:
        - intellij-idea-community-edition
        - visual-studio-code
'''


RETURN = r'''
#
'''


import textwrap
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.validation import (check_type_dict, check_type_list, check_type_str)


class CheckTypeConfig:
    def __init__(self):
        self.__name__ = 'str'

    def __call__(self, config):
        return check_type_str(config)


class CheckTypePackages:
    def __init__(self):
        self.__name__ = 'dict[str,list[str]]'

    def __call__(self, packages):
        packages = check_type_dict(packages)
        for channel, names in packages.items():
            channel = check_type_str(channel)
            names = check_type_list(names)
            for name in names:
                name = check_type_str(name)
        return packages


class NixEnv:
    def __init__(self):
        self.module = AnsibleModule(
            argument_spec={
                'config': {
                    'default': '{}',
                    'type': CheckTypeConfig(),
                },
                'packages': {
                    'required': True,
                    'type': CheckTypePackages(),
                },
            },
            supports_check_mode=True,
        )

        self.result = {
            'changed': False
        }

    def make_config(self, config=None):
        if config is None:
            config = self.module.params['config']

        content = config.encode('utf-8')

        try:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(content)
                return f.name
        except Exception as e:
            msg = str(e)
            self.module.fail_json(msg)

    def make_defexpr(self, packages=None):
        if packages is None:
            packages = self.module.params['packages']

        lblock = []
        iblock = []
        for channel, names in packages.items():
            lexpr = '{channel} = import <{channel}> {args};'.format(channel=channel, args='{}')
            lblock.append(lexpr)
            iexpr = 'inherit ({channel}) {names};'.format(channel=channel, names=' '.join(names))
            iblock.append(iexpr)

        content = textwrap.dedent('''\
            let
              {lblock}
            in {{
              {iblock}
            }}
        ''')
        content = content.format(lblock='\n  '.join(lblock), iblock='\n  '.join(iblock))
        content = content.encode('utf-8')

        try:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(content)
                return f.name
        except Exception as e:
            msg = str(e)
            self.module.fail_json(msg)

    def run_install(self, config_path=None, defexpr_path=None):
        if config_path is None:
            config_path = self.make_config()
        if defexpr_path is None:
            defexpr_path = self.make_defexpr()

        dry_run = ('--dry-run') if self.module.check_mode else ()

        args = [self.bin_path, *dry_run, '-f', defexpr_path, '-ir']
        self.module.log("'{}'".format("' '".join(args)))

        _, stdout, stderr = self.module.run_command(args, check_rc=True, environ_update={'NIXPKGS_CONFIG': config_path})
        self.module.debug(stdout)
        self.module.debug(stderr)

        if not dry_run:
            self.result['changed'] = True

    def run(self):
        self.bin_path = self.module.get_bin_path('nix-env', required=True, opt_dirs=['/nix/var/nix/profiles/default/bin'])
        self.run_install()
        self.module.exit_json(**self.result)


def main():
    nix_env = NixEnv()
    nix_env.run()


if __name__ == '__main__':
    main()
