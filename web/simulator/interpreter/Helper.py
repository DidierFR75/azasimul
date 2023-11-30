import os
from .InputAnalyzer import InputAnalyzer
import pathlib
import zipfile

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