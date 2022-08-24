from openpyxl import Workbook, load_workbook
from openpyxl.writer.excel import save_virtual_workbook
import os
import pandas as pd


class InputAdaptater:

    def __init__(self, input) -> None:
        self.input = input
        self.json = {}


    def _getRawDataStorage(self):
        """
            Return JSON storage of the input
        """
        ws = load_workbook(os.getcwd()+ "/input/model.xlsx")
        df = pd.read_excel(self.input, engine='openpyxl')

        return df.sheet_names
        
if __name__ == "__main__":
    ia = InputAdaptater("./input/model.xlsx")
    print(ia._getRawDataStorage())