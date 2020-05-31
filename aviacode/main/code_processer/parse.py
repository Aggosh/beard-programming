import time
import sys
import multiprocessing.pool
import functools
import random
import string
import importlib
import os
import errno

from decimal import Decimal


TIMEOUT = 5


def timeout(max_timeout):
    """Timeout decorator, parameter in seconds."""

    def timeout_decorator(item):
        """Wrap the original function."""

        @functools.wraps(item)
        def func_wrapper(*args, **kwargs):
            """Closure for function."""
            pool = multiprocessing.pool.ThreadPool(processes=1)
            async_result = pool.apply_async(item, args, kwargs)
            # raises a TimeoutError if execution exceeds max_timeout
            return async_result.get(max_timeout)

        return func_wrapper

    return timeout_decorator


class Parser:
    def __init__(self, username, folder="parse_code", additional_filename_random=8):
        self.folder = folder
        self.username = username
        self.additional_filename_random = additional_filename_random

    def save_code(self, code: str) -> str:
        self.filename = f"{self.username}_{self._randomString()}.py"

        self.code_file_path = f"{self.folder}/{self.filename}"

        if True:
            code +='''
    from typing import Union
    import resource

    def humanize_bytes(num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def process_ram_usage(human_readable: bool = True) -> Union[str, int]:
        bytes_ram = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return bytes_ram if not human_readable else humanize_bytes(bytes_ram)

    return(process_ram_usage(human_readable=True))
        '''

        if not os.path.exists(os.path.dirname(self.code_file_path)):
            try:
                os.makedirs(os.path.dirname(self.code_file_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(self.code_file_path, "w+") as file:
            file.write(code)

        return self.code_file_path

    @timeout(TIMEOUT)
    def process_code(self) -> tuple:
        """
        process the code file
        return tuple of:
                process_result is None,
                process_time in str,
                process_output is  str,
                memory_usage in str
            if Exception return:
                exception in str,
                process_time in None,
                process_output is None,
                memory_usage is None
        if process run latter then 5 seconds rise TimeoutError
        """

        self.output_path = f"{self.code_file_path}_output.txt"
        orig_stdout = sys.stdout
        output = open(self.output_path, "w")
        sys.stdout = output

        try:

            module_path = self.code_file_path.replace(
                "/", ".").replace(".py", "")

            test_module = importlib.import_module(module_path)

            time_start = Decimal(time.perf_counter())

            memory_usage = test_module.tests()

            process_time = str(Decimal(time.perf_counter()) - time_start)

            process_result = None

        except Exception as e:
            process_result = e
            process_time = None
            memory_usage = None

        sys.stdout = orig_stdout
        output.close()
        with open(self.output_path, "r") as file:
            process_output = file.read().replace("\n", "")

        return process_result, process_time, process_output, memory_usage

    def delete_files(self):
        os.remove(self.code_file_path)
        os.remove(self.output_path)

    def _randomString(self):
        letters = string.ascii_lowercase
        return "".join(
            random.choice(letters) for i in range(self.additional_filename_random)
        )

    def __str__(self):
        return self.username
