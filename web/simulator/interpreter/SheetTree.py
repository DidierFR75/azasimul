import os
import pandas as pd
import numpy as np
import scipy as sp
from scipy import interpolate
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from pycel import ExcelCompiler
from openpyxl import Workbook, load_workbook
from anytree import Node, find, findall
from copy import copy, deepcopy
from faker import Faker
from .InputAnalyzer import InputAnalyzer
from .Helper import Helper

import logging
import os
try:
    logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': './logs/log.log'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
})
    os.makedirs('./logs', exist_ok=True)
    logger = logging.getLogger(__name__)
except Exception as e:
    print(e)

class SheetTree:
    """
    The `SheetTree` class is responsible for creating a tree structure to organize and analyze sheets in Excel workbooks.

    Attributes:
        path (str): The path to the folder containing the Excel workbooks.
        root (Node): The root node of the formula tree.
        all_sheet (dict): A dictionary with the file names as keys and a list of sheet analyzers as values.
        operation_sheets (list): A list of sheet analyzers for the operation sheets.
    """
    def __init__(self, path) -> None:
        """
        Initializes a new instance of the SheetTree class.
        
        Args:
            path (str): The path to the folder containing the Excel workbooks.
        """
        self.path = path
        
        self.root = Node("root")
        self.root.name = "Summary"
        self.root.categories = {}

        self.all_sheet = None
        self.operation_sheets = []
    def readAllSheetsFromFolder(self, folder):
        """
        Reads all the sheets from a folder and returns a dictionary with the file names as keys and a list of sheet analyzers as values.
        
        Args:
            folder (str): The path to the folder containing the Excel workbooks.
        
        Returns:
            dict: A dictionary with the file names as keys and a list of sheet analyzers as values.
        """
        result = {}

        # Load all workbooks
        all_files = next(os.walk(folder), (None, None, []))[2]
        all_files = [ fn for fn in all_files if not Helper.rejectXlsFile(fn) ]
        all_wks = { file: load_workbook(folder +'/'+ file) for file in all_files }
        
        # Create dict with file: {sheetname: analyzer}
        for file, wb in all_wks.items():
            result[file] = []
            for sheet_name in wb.sheetnames:
                if sheet_name.startswith(InputAnalyzer.DELIMITER_SHEET_UNFOLLOW):
                    logger.info(f"Sheet('{sheet_name}') : SKIPPED")
                    continue
                analyzer = InputAnalyzer(wb[sheet_name], sheet_name, folder + '/' + file)
                if analyzer.loadSheet():
                    result[file].append((sheet_name, analyzer,))

        return result

    def mapSheetsToFormulaTree(self, path=None):
        """
        Maps the sheets to the formula tree structure.
        
        Args:
            path (str, optional): The path to the folder containing the Excel workbooks. If not provided, uses the default path.
        """
        if not path:
            path = self.path
        nodes = []
        self.all_sheet = self.readAllSheetsFromFolder(path)
        # Create all nodes
        for _file, wbSheets in self.all_sheet.items():
            for sheet_name, analyzer in wbSheets:
                if analyzer.isOperationSheet():
                    self.operation_sheets.append(analyzer)
                    continue
            
                if analyzer.isConstantSheet():
                    Node(sheet_name, analyzer=analyzer, parent=self.root)
                    continue

                if analyzer.isSummarySheet():
                    if not hasattr(self.root, "analyzer"):
                        self.root.analyzer = analyzer
                    else:
                        # Delete summary value with same key that root_summary
                        for root_summary in self.root.analyzer.summary:
                            for summary in analyzer.summary:
                                if root_summary["summary_name"].lower() == summary["summary_name"].lower():
                                    del summary
                        # Merge summaries values
                        for summary in analyzer.summary:
                            self.root.analyzer.summary.append(summary)
                                                        
                    continue

                if analyzer.metadatas == {}:
                    continue
                
                # last Case is a "Curves" sheet
                # Get parent name if exists
                parentName = analyzer.metadatas[analyzer.PRODUCT_PARENT] if (analyzer.PRODUCT_PARENT in analyzer.metadatas) else None
                    
                productType = analyzer.metadatas[analyzer.PRODUCT_NAME]
                node = Node(productType, analyzer=analyzer)
                
                # Get and add category to self.root.categories if exist
                category = analyzer.getCategory()
                if category is not None:
                    self.root.categories[category.lower()] = category.upper()+":"
                    node.category = category.lower()
                                            
                nodes.append( (parentName, productType, node ) )
        
        # Add parent for all nodes
        for element in nodes:
            if element[0] is None: # if no parentName
                element[2].parent = self.root
            else:
                i = [i for i, v in enumerate(nodes) if v[1] == element[0] and element[2].category == v[2].category]
                if i != []:
                    element[2].parent = nodes[i[0]][2]
