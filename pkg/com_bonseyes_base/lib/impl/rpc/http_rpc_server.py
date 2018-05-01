import json
from typing import Dict, Any, Union, Callable, List

from flask import jsonify
from flask.app import Flask
from flask.globals import request
from flask.helpers import send_file, make_response
from flask.wrappers import Response
from functools import wraps
from io import BytesIO, FileIO
from types import GeneratorType

from ...api.storage import StorableObject
from ...api.utils import NamedObjectMap, OrderedNamedObjectList
from ...api.values import PlainObjectType
from ..values.memory_values import PlainObjectValueFromMemory, UrlValueFromMemory, \
    ResourceValueFromMemory, \
    ResourceValueFromStream, ArchiveValueFromUrl, ArchiveValueFromStream


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


def add_arg_by_name(arguments: Dict, name: str, value: Any) -> None:
    parts = name.split('.')

    store = arguments

    for part in parts[:-1]:
        if part not in store:
            store[part] = {}
        store = store[part]

    store[parts[-1]] = value


def parse_http_parameters():

    arguments = {}

    for name, value in request.form.items():
        add_arg_by_name(arguments, name, value)

    for name, part in request.files.items():

        if part.content_type == 'application/vnd.com.bonseyes.data+plainobject':
            data = json.load(part.stream)
            value = PlainObjectValueFromMemory(data)
        elif part.content_type == 'application/vnd.com.bonseyes.data+string':
            stream = BytesIO()
            part.save(stream)
            value = PlainObjectValueFromMemory(stream.getvalue().decode('utf-8'))
        elif part.content_type == 'application/vnd.com.bonseyes.data+url':
            stream = BytesIO()
            part.save(stream)
            value = UrlValueFromMemory(stream.getvalue().decode('utf-8'))
        elif part.content_type == 'application/vnd.com.bonseyes.data+resource.url':
            stream = BytesIO()
            part.save(stream)
            value = ResourceValueFromMemory(url=stream.getvalue().decode('utf-8'))
        elif part.content_type == 'application/vnd.com.bonseyes.data+resource.blob':
            value = ResourceValueFromStream(stream=part.stream)
        elif part.content_type == 'application/vnd.com.bonseyes.data+archive.url':
            stream = BytesIO()
            part.save(stream)
            value = ArchiveValueFromUrl(url=stream.getvalue().decode('utf-8'))
        elif part.content_type == 'application/vnd.com.bonseyes.data+archive.blob':
            value = ArchiveValueFromStream(stream=part.stream)
        else:
            raise Exception("Invalid content type " + part.content_type)

        add_arg_by_name(arguments, name, value)

    return arguments


def is_follow_request():
    return request.headers.get('X-Bonseyes-Follow') == 'true'


class DataWithMimeType:
    def __init__(self, data: Any, mimetype: str):
        self.data = data
        self.mimetype = mimetype


def create_answer(result: Union[StorableObject, PlainObjectType,
                                NamedObjectMap, OrderedNamedObjectList,
                                str, DataWithMimeType], mimetype: str=None):

    # change parameters if we received data with mimetype
    if isinstance(result, DataWithMimeType):
        mimetype = result.mimetype
        result = result.data

    # send the data in the appropriate way
    if isinstance(result, StorableObject):
        return jsonify(result.to_dict())

    elif isinstance(result, Dict) or isinstance(result, List):
        return jsonify(result)

    elif isinstance(result, NamedObjectMap):
        return jsonify(result.names)

    elif isinstance(result, OrderedNamedObjectList):
        return jsonify({'names': result.names, 'count': result.count})

    elif isinstance(result, str):
        return result, 200, {'Content-Type': mimetype or 'text-plain'}

    elif isinstance(result, bool):
        return result and "true" or "false", 200, {'Content-Type': mimetype or 'text-plain'}

    elif isinstance(result, FileIO):
        return send_file(result, mimetype=(mimetype or 'application/binary'))

    elif hasattr(result, 'read'):

        def generator():
            while True:

                next_data = result.read(1024*1024)

                if next_data is None or len(next_data) == 0:
                    return

                yield next_data

        return Response(generator(), mimetype=(mimetype or 'application/binary'))

    elif isinstance(result, bytes):
        return result

    elif isinstance(result, GeneratorType):
        return Response(result, mimetype=(mimetype or 'application/binary'))

    else:
        raise Exception("Cannot send type " + str(type(result)))


def publish_data(app: Flask, path: str, mimetype: str=None):

    def decorator(producer: Callable[..., Union[StorableObject, PlainObjectType,
                                                NamedObjectMap, OrderedNamedObjectList,
                                                str]]):
        @no_cache()
        @wraps(producer)
        def handler(**kwargs):
            result = producer(**kwargs)
            return create_answer(result, mimetype=mimetype)

        app.add_url_rule(path, view_func=handler)

        return handler

    return decorator


def publish_method(app: Flask, path: str):

    def decorator(handler: Callable[..., Union[StorableObject, PlainObjectType,
                                               NamedObjectMap, OrderedNamedObjectList,
                                               str]]):
        @no_cache()
        @wraps(handler)
        def wrapped_handler(**kwargs):

            arguments = parse_http_parameters()

            result = handler(arguments=arguments, **kwargs)

            return create_answer(result)

        app.add_url_rule(path, view_func=wrapped_handler, methods=['POST'])

        return handler

    return decorator


def publish_delete(app: Flask, path: str):

    def decorator(handler: Callable[..., None]):

        @no_cache()
        @wraps(handler)
        def wrapped_handler(**kwargs):

            handler(**kwargs)

            return jsonify({'result': 'success'})

        app.add_url_rule(path, view_func=wrapped_handler, methods=['DELETE'])

        return handler

    return decorator
