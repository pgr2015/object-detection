#!/usr/bin/env python3
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
import os

HASHBANG = "#!/usr/bin/env python3\n"

COPYING_JS = """/**
 *
 * NVISO CONFIDENTIAL
 * 
 * Copyright (c) 2017 nViso SA. All Rights Reserved.
 * 
 * The source code contained or described herein and all documents related to
 * the source code ("Material") is the confidential and proprietary information
 * owned by nViso or its suppliers or licensors.  Title to the  Material remains
 * with nViso SA or its suppliers and licensors. The Material contains trade
 * secrets and proprietary and confidential information of nViso or its
 * suppliers and licensors. The Material is protected by worldwide copyright and trade
 * secret laws and treaty provisions. You shall not disclose such Confidential
 * Information and shall use it only in accordance with the terms of the license
 * agreement you entered into with nViso.
 *
 * NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
 * THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
 * TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 * PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
 * ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
 * DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
 *
 */
"""

COPYING_PY = """#
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
"""

COPYING_HTML = """<!--

 NVISO CONFIDENTIAL

 Copyright (c) 2017 nViso SA. All Rights Reserved.

 The source code contained or described herein and all documents related to
 the source code ("Material") is the confidential and proprietary information
 owned by nViso or its suppliers or licensors.  Title to the  Material remains
 with nViso SA or its suppliers and licensors. The Material contains trade
 secrets and proprietary and confidential information of nViso or its
 suppliers and licensors. The Material is protected by worldwide copyright and trade
 secret laws and treaty provisions. You shall not disclose such Confidential
 Information and shall use it only in accordance with the terms of the license
 agreement you entered into with nViso.

 NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
 THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
 TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
 ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
 DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.

-->
"""

for dirpath, dirnames, filenames in os.walk('.'):

    # don't go inside the virtualenv if present
    if dirpath == '.' and 'env' in dirnames:
        dirnames.remove('env')

    # skip the .git folder
    if '.git' in dirnames:
        dirnames.remove('.git')

    for file_name in filenames:

        file_path = os.path.join(dirpath, file_name)

        if file_name.endswith('.py') or file_name.endswith('.yml') or file_name == 'Dockerfile':

            with open(file_path) as fp:
                contents = fp.read()

            with_hashbang = False
            if contents.startswith(HASHBANG):
                contents = contents[len(HASHBANG):]
                with_hashbang = True

            if contents.startswith(COPYING_PY):
                continue

            print("Fixing copyright on " + file_path)

            with open(file_path, 'w') as fp:
                if with_hashbang:
                    fp.write(HASHBANG)
                fp.write(COPYING_PY)
                fp.write(contents)

        elif file_name.endswith('.html'):

            with open(file_path) as fp:
                contents = fp.read()

            if contents.startswith(COPYING_HTML):
                continue

            print("Fixing copyright on " + file_path)

            with open(file_path, 'w') as fp:
                fp.write(COPYING_HTML)
                fp.write(contents)

        elif file_name.endswith('.js'):

            with open(file_path) as fp:
                contents = fp.read()

            if contents.startswith(COPYING_JS):
                continue

            print("Fixing copyright on " + file_path)

            with open(file_path, 'w') as fp:
                fp.write(COPYING_JS)
                fp.write(contents)
