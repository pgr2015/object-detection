import time
import typing
from typing import IO, Callable, Generator

import importlib
import tarfile
import subprocess
import logging
from io import BytesIO
from tarfile import TarInfo

from ..api.storage import Storage


def load_callable(full_callable_name):

    if full_callable_name is None:
        return None

    package_name, callable_name = full_callable_name.split(':')

    package = importlib.import_module(package_name)

    return getattr(package, callable_name)


class GeneratorReader:

    def __init__(self, it: Generator):
        self.it = it
        self._buffer = b""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def read(self, n=-1):

        if self._buffer is None:
            return None

        if n == -1:

            output = BytesIO()

            for data in self.it:
                output.write(data)

            return output.getvalue()

        else:

            try:

                while len(self._buffer) < n:
                    self._buffer = self._buffer + next(self.it)

                ret = self._buffer[:n]
                self._buffer = self._buffer[n:]
                return ret

            except StopIteration:
                ret = self._buffer
                self._buffer = None
                return ret


class TarBuilder:

    def __init__(self, storage: Storage):
        self.pos = 0
        self.output_stream = None

        class OutputStream:
            def __init__(self):
                self.pos = 0
                self.buffer = BytesIO()

            def tell(self):
                return self.pos

            def write(self, data):
                self.pos += len(data)
                self.buffer.write(data)

            def flush(self):
                pass

        self.output_stream = OutputStream()
        self._data_generator = self._open(storage)

    def drain_data(self) -> bytes:
        data = self.output_stream.buffer.getvalue()
        self.output_stream.buffer.seek(0)
        self.output_stream.buffer.truncate()
        return data

    @property
    def available_data_len(self) -> int:
        return self.output_stream.buffer.tell()

    def generate_next_data(self) -> None:
        next(self._data_generator)

    def _open(self, storage: Storage) -> Generator:

        with tarfile.open(fileobj=self.output_stream, mode='w') as tar:

            dirs = ['']

            while len(dirs) > 0:

                next_dir = dirs.pop(0)

                for entry_name in storage.list(next_dir):

                    full_path = next_dir + '/' + entry_name

                    if storage.isdir(full_path):
                        dirs.append(full_path)
                    else:
                        with storage.open(full_path, mode='rb') as fp:
                            tar_info = TarInfo(name=full_path.lstrip('/'))

                            fp.seek(0, 2)
                            tar_info.size = fp.tell()
                            fp.seek(0)

                            tar.addfile(tar_info, fp)

                        yield


class TarBuilderReader:

    def __init__(self, builder: TarBuilder):
        self._builder = builder
        self._buffer = b''

    def read(self, n=-1):
        if self._buffer is None:
            return None

        if n == -1:
            raise Exception("Not implemented")

        try:

            while self._builder.available_data_len + len(self._buffer) < n:
                self._builder.generate_next_data()

            self._buffer = self._buffer + self._builder.drain_data()

            ret = self._buffer[:n]
            self._buffer = self._buffer[n:]
            return ret

        except StopIteration:
            ret = self._buffer + self._builder.drain_data()
            self._buffer = None
            return ret

    def close(self):
        pass


class TarStream:

    def __init__(self, stream):
        self.pos = 0
        self.stream = stream

    def read(self, size=-1):
        data = self.stream.read(size)
        self.pos += len(data)
        return data

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):

        if whence == 0:
            if offset < self.pos:
                raise Exception("Cannot seek to %d" % offset)

            if offset != self.pos:
                self.read(offset - self.pos)

        if whence == 1:
            if offset < 0:
                raise Exception("Cannot seek to %d from current position" % offset)

            if offset == 0:
                return

            self.read(offset)

        if whence == 2:
            raise Exception("Cannot seek to %d from end of file" % offset)


def follow_file(fp: IO, condition: Callable[[], bool]) -> typing.Generator:

    def data_generator():

        try:

            where = 0

            # follow file while the condition is true
            while condition():
                where = fp.tell()
                line = fp.readline()
                if not line:
                    time.sleep(1)
                    fp.seek(where)
                else:
                    yield line

            # output the remaining data
            fp.seek(where)

            while True:
                data = fp.read(1024*1024)

                if data == '':
                    break

                yield data

        finally:
            fp.close()

    return data_generator()


def execute_with_logs(*args, cwd=None):
    # start the process with stderr sent to stdout and stdout redirected to
    process = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # print out the logs while they happen
    for line in process.stdout:
        logging.info("command: " + line.decode('utf-8', 'ignore').strip())

    # wait for process to terminate
    process.wait()

    # check process return code
    if process.returncode != 0:
        raise Exception("Error while executing %s (exit code %d)" % ( args[0], process.returncode))
