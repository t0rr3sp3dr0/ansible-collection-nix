#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2023, Pedro Tôrres <t0rr3sp3dr0@gmail.com>
# Apache License 2.0 (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
module: channel
description: >
  A Nix channel is a mechanism that allows you to automatically stay up-to-date
  with a set of pre-built Nix expressions. A Nix channel is just a URL that
  points to a place containing a set of Nix expressions.
short_description: manage Nix channels
version_added: 0.0.2
author:
  - Pedro Tôrres (@t0rr3sp3dr0)
options:
  channels:
    description: URLs of each channel.
    required: true
    type: dict[str,str]
'''


EXAMPLES = r'''
- name: nix_channel
  t0rr3sp3dr0.nix.channel:
    channels:
      nixpkgs: https://nixos.org/channels/nixpkgs-unstable
      t0rr3sp3dr0: https://github.com/t0rr3sp3dr0/nixpkgs/archive/HEAD.tar.gz
'''


RETURN = r'''
#
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.validation import (check_type_dict, check_type_str)


class CheckTypeChannels:
    def __init__(self):
        self.__name__ = 'dict[str,str]'

    def __call__(self, channels):
        channels = check_type_dict(channels)
        for name, url in channels.items():
            name = check_type_str(name)
            url = check_type_str(url)
        return channels


class NixChannel:
    def __init__(self):
        self.module = AnsibleModule(
            argument_spec={
                'channels': {
                    'required': True,
                    'type': CheckTypeChannels(),
                },
            },
            supports_check_mode=True,
        )

        self.result = {
            'changed': False
        }

    def run_list(self):
        args = [self.bin_path, '--list']
        self.module.log("'{}'".format("' '".join(args)))

        _, stdout, stderr = self.module.run_command(args, check_rc=True)
        self.module.debug(stdout)
        self.module.debug(stderr)

        lines = stdout.splitlines()
        return [tuple(line.split(maxsplit=1)) for line in lines]

    def run_remove(self, channels=None):
        if channels is None:
            channels = self.run_list()

        if self.module.check_mode:
            return

        self.result['changed'] = True

        for name, _ in channels:
            args = [self.bin_path, '--remove', name]
            self.module.log("'{}'".format("' '".join(args)))

            _, stdout, stderr = self.module.run_command(args, check_rc=True)
            self.module.debug(stdout)
            self.module.debug(stderr)

    def run_add(self, channels=None):
        if channels is None:
            channels = self.module.params['channels'].items()

        if self.module.check_mode:
            return

        self.result['changed'] = True

        for name, url in channels:
            args = [self.bin_path, '--add', url, name]
            self.module.log("'{}'".format("' '".join(args)))

            _, stdout, stderr = self.module.run_command(args, check_rc=True)
            self.module.debug(stdout)
            self.module.debug(stderr)

    def run_update(self):
        if self.module.check_mode:
            return

        self.result['changed'] = True

        args = [self.bin_path, '--update']
        self.module.log("'{}'".format("' '".join(args)))

        _, stdout, stderr = self.module.run_command(args, check_rc=True)
        self.module.debug(stdout)
        self.module.debug(stderr)

    def run(self):
        self.bin_path = self.module.get_bin_path('nix-channel', required=True, opt_dirs=['/nix/var/nix/profiles/default/bin'])
        self.run_remove()
        self.run_add()
        self.run_update()
        self.module.exit_json(**self.result)


def main():
    nix_channel = NixChannel()
    nix_channel.run()


if __name__ == '__main__':
    main()
