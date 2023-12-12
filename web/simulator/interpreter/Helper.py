import os
from .InputAnalyzer import InputAnalyzer
import pathlib
import zipfile

import time
from functools import wraps

_total_time_call_stack = [0]
    
def better_time_tracker(log_fun):
    def _better_time_tracker(fn):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            global _total_time_call_stack
            _total_time_call_stack.append(0)
            
            start_time = time.time()
            
            try:
                result = fn(*args, **kwargs)
            finally:
                elapsed_time = time.time() - start_time
                inner_total_time = _total_time_call_stack.pop()
                partial_time = elapsed_time - inner_total_time

                _total_time_call_stack[-1] += elapsed_time
                
                # log the result
                log_fun({
                    'function_name': fn.__name__,
                    'total_time': elapsed_time,
                    'partial_time': partial_time,
                })

            return result

        return wrapped_fn
    return _better_time_tracker

class Helper:
    @staticmethod
    def rejectXlsFile(fn):
        """
        Check if a given file name is valid for processing.

        Args:
            fn (str): The file name to be checked.

        Returns:
            bool: True if the file name is invalid, False if the file name is valid.

        Example:
            >>> file_name = "example.xlsx"
            >>> result = rejectXlsFile(file_name)
            >>> print(result)
            False

            >>> file_name = ".hidden.xlsx"
            >>> result = rejectXlsFile(file_name)
            >>> print(result)
            True
        """
        if fn.startswith(".") or fn.startswith(InputAnalyzer.DELIMITER_SHEET_UNFOLLOW) or not fn.endswith('.xlsx'):
            return True
        return False
    
    @staticmethod
    def reject_file(file_path):
        """
        Check if a given file path is valid for processing.

        Args:
            file_path (str): The path of the file to be checked.

        Returns:
            bool: True if the file path is invalid, False if the file path is valid.
        """
        fn = os.path.basename(file_path)
        if Helper.rejectXlsFile(fn):
            return True
        return False
    
    @staticmethod
    def folder_zip(folderPath, zip_fn):
        """
        Create a zip file of a given folder.

        Args:
            folderPath (str): The path of the folder to be zipped.
            zip_fn (str): The filename of the generated zip file.

        Returns:
            str: The path of the generated zip file.
        """
        directory = pathlib.Path(folderPath)
        destination = f"{directory.parent.absolute()}/{zip_fn}.zip"

        with zipfile.ZipFile(destination, mode="w") as archive:
            for file_path in directory.iterdir():
                if Helper.reject_file(file_path):
                    continue
                archive.write(file_path, arcname=file_path.name)
        return destination