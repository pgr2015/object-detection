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
    parser = argparse.ArgumentParser('Bonseyes client tool')

    if 'BONSEYES_GATEWAY_HOST' in os.environ:
        default_gateway_host = os.environ['BONSEYES_GATEWAY_HOST']
    else:
        default_gateway_host = 'localhost'

    if 'BONSEYES_GATEWAY_PORT' in os.environ:
        default_gateway_port = os.environ['BONSEYES_GATEWAY_PORT']
    else:
        default_gateway_port = '8000'

    parser.add_argument('--gateway-port', default=default_gateway_port, help="Port where the gateway is "
                        "listening (default: 8000)")
    parser.add_argument('--gateway-host', default=default_gateway_host, help="Host where the gateway" +
                        "can be reached (default: localhost)")

    subparsers = parser.add_subparsers(dest='object')
    subparsers.required = True

    commands = ['artifact', 'artifact_container', 'build', 'pipeline_container', 'run', 'start']

    for command in commands:
        importlib.import_module('bonseyes_client.commands.' + command).setup_parser(subparsers)

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
