#
# NVISO CONFIDENTIAL
#
# Copyright (c) 2017 nViso SA. All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") is the confidential and proprietary information
# owned by nViso or its suppliers or licensors.  Title to the  Material remains
# with nViso SA or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of nViso or its
# suppliers and licensors. The Material is protected by worldwide copyright and trade
# secret laws and treaty provisions. You shall not disclose such Confidential
# Information and shall use it only in accordance with the terms of the license
# agreement you entered into with nViso.
#
# NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
# THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
# DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
#


import argparse
import importlib

import os


def main():

    parser = argparse.ArgumentParser('Bonseyes client tool', allow_abbrev=False)

    if 'BE_ENVIRONMENT' in os.environ:
        default_env = os.environ['BE_ENVIRONMENT']
    else:
        default_env = None

    parser.add_argument(
        '--environment', default=default_env, help="Environment to use")

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    commands = ['run', 'ps', 'status', 'rm', 'build', 'step_log', 'retry', 'save']

    for command in commands:
        importlib.import_module('.commands.' + command, package=__package__).setup_parser(parser, subparsers)

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
