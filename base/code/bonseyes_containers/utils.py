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
import importlib
import os

from functools import wraps
from flask import make_response


def no_cache():
    """This decorator adds the Cache-Control no-store to the response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            resp.cache_control.no_store = True
            resp.cache_control.max_age = 0
            resp.cache_control.no_cache = True
            resp.cache_control.must_revalidate = True
            return resp
        return decorated_function
    return decorator


def force_revalidate(file_path):
    """This decorator adds the max_age=0 to force revalidation and set the last modified timestamp of a file"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            resp.cache_control.max_age = 0
            resp.last_modified = int(os.path.getmtime(file_path))
            return resp
        return decorated_function
    return decorator


def load_callable(full_callable_name):

    if full_callable_name is None:
        return None

    package_name, callable_name = full_callable_name.split(':')

    package = importlib.import_module(package_name)

    return getattr(package, callable_name)


def get_full_name(obj):
    return obj.__module__ + ':' + obj.__qualname__
