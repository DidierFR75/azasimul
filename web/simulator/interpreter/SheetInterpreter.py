import os
import re
import random
import pathlib
import zipfile
import datetime
import copy
import logging
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
from .SheetTree import SheetTree
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
class SheetInterpreter:
    """
    The `SheetInterpreter` class is responsible for interpreting and evaluating formulas in Excel workbooks. 
    It replaces variables and functions in the formulas with their corresponding values and then evaluates the formulas to obtain the final results.

    Main functionalities:
    - Replaces variables and functions in formulas with their corresponding values
    - Evaluates the formulas to obtain the final results
    - Updates the summary and curves sheets in the Excel workbooks with the evaluated results

    Methods:
    - __init__(self, folder): Initializes a new instance of the SheetInterpreter class with the specified folder path.
    - findOperation(self, category, operation_name): Finds an operation by its category and operation name.
    - convertFilter(self, value, unit, filter): Converts a value based on a filter.
    - replaceOneVarByValue(self, word, default_node, category, scope): Replaces a variable in a formula with its corresponding value.
    - replaceAllVarsByValue(self, opStr, default_node, category, scope): Replaces all variables in a formula with their corresponding values.
    - replaceFcnByVar(self, opStr, category, scope): Replaces functions in a formula with their corresponding values.
    - mapOperationValues(self, list_operations, category, scope): Maps the values in a list of operations by replacing variables and functions with their corresponding values.
    - operationParser(self): Parses the operations by replacing functions with variables and mapping the values.
    - evaluate(self): Evaluates the formulas by replacing variables and functions with their values and updating the summary and curves sheets.

    Fields:
    - tree: The SheetTree object that represents the tree structure of the Excel workbooks.
    - node_categories: A list of the categories of the nodes in the tree.
    - operations: A dictionary that stores the evaluated operations categorized by node category.
    """
    FILTERS_DISPATCH = {
        "date" : {
            "year" : lambda x: x.year,
            "month": lambda x: x.month,
            "day": lambda x: x.day
        }
    }

    FCN_EXPR = '\{[ \_\(\)\-\|\.a-zA-Z0-9!]+\}'
    VAR_EXPR = '\[[ \_\(\)\|\-\+a-zA-Z0-9\.!]+\]'
    FLOAT_PRECISION = 4

    def __init__(self, folder) -> None:
        self.tree = SheetTree(folder)
        self.tree.mapSheetsToFormulaTree()
        self.node_categories = list(self.tree.root.categories.keys()) # list(map(lambda x: x.lower(), list(self.tree.root.categories.keys())))
        self.operations = {cat: [] for cat in self.node_categories}
        self.operations["root"] = []
    
    # Utils functions

    def findNode(self, treeRoot, category, scope, verbose=False):
        """
        Find the first node in a tree structure based on its category and scope.

        Args:
            treeRoot (Node): The root node of the tree structure.
            category (str): The category of the node to find.
            scope (str): The scope of the node to find.
            verbose (bool, optional): Whether to log errors if multiple nodes are found. Defaults to False.

        Returns:
            Node: The first matching node found in the tree based on the given category and scope.

        Raises:
            Exception: If the node with the given category and scope is not found in the tree.
        """
        catCode = category.lower()
        nodes = None
        if scope:
            nodes = findall(treeRoot, lambda node: node.name.lower() == catCode and hasattr(node, 'category') and node.category == scope)
            if not nodes and scope == "root":
                nodes = findall(treeRoot, lambda node: node.name.lower() == catCode and not hasattr(node, 'category'))
            if len(nodes)>1 and verbose:
                logger.error(f"!!! nodes_according_to_category({catCode}) Scope({scope}).length()>1")
        if not nodes:
            nodes = findall(treeRoot, lambda node: node.name.lower() == catCode) 
            if not nodes:
                raise Exception(f"Cannot find sheet '{catCode}' in the tree... with Scope '{scope}'")

        node = nodes[0] if nodes else nodes
        return node

    def findOperation(self, category, operation_name):
        """
        Find an operation by it category and it operation_name 
        """
        for analyzer in self.tree.operation_sheets:
            for analyzer_category, operations in analyzer.operations.items():
                if analyzer_category.lower() == category.lower():
                    return next((operation for operation in operations if operation["operation_name"].lower() == operation_name.lower()), None)
        return None

    def convertFilter(self, value, unit, filter):
        """
        Convert value by it filter
        Ex : datetime(01/01/2022)|year = 2022
        """
        try:
            func = self.FILTERS_DISPATCH[unit.lower()][filter.lower()]
            value = func(value)
        except: pass
        return value

    # Functions to search and replace variables and functions

    ## replaceOneVarByValue
    def replaceOneVarByValue(self, word, default_node, category, scope, position=0):
        if word is None or category is None:
            raise Exception("replaceOneVarByValue needs all parameters to be filled.")

        correct_word, line_number = self._extract_correct_word_and_line(word)
        attr = self._parse_variable_name(correct_word, category)
        node = self._find_appropriate_node(attr, default_node, scope)
        
        return self._get_variable_value(node, attr, line_number, position)

    def _extract_correct_word_and_line(self, word):
        correct_word = word.strip("[]")
        line_number = None
        if '!' in correct_word:
            correct_word, line_info = re.match(r'(.*?)!(\d+)', correct_word).groups()
            line_number = int(line_info)
        return correct_word, line_number

    def _parse_variable_name(self, word, category):
        attr = word.split('.')
        if len(attr) == 1:
            attr.insert(0, category)
        return attr

    def _find_appropriate_node(self, attr, default_node, scope):
        if len(attr) > 1:
            return self.findNode(self.tree.root, attr[0], scope)
        else:
            return default_node

    def _get_variable_value(self, node, attr, line_number, position=0):
        if node.analyzer.isConstantSheet():
            constant = node.analyzer.getConstantByCategoryAndName(attr[1], attr[2])
            return constant["value"] if constant else None

        if node.analyzer.isSummarySheet():
            cw = attr[1].split('|')
            summary = node.analyzer.getSummaryByName(cw[0])

            if summary:
                return self.convertFilter(summary["summary_value"], summary["unit"], cw[1]) if len(cw) == 2 else summary["summary_value"]
            return None

        if node.analyzer.isCurvesSheet():
            spec = node.analyzer.getCurveByName(attr[1])
            if spec:
                if spec["interpolation"] == "CONST":
                    return spec["values"][0]
                else:
                    try:
                        return spec["values"][line_number] if line_number is not None and line_number <= len(spec["values"]) else spec["values"][position]
                    except Exception as e:
                        raise Exception(f"Can't access data values for {spec}: {e}")
            else:
                raise Exception(f'No curve found with name {attr[1]} in {node.name}')

        return None

    ## replaceAllVarsByValue
    def replaceAllVarsByValue(self, opStr, default_node, category, scope, position=0):
        """
        Replaces all variables in a formula string with their corresponding values.

        Args:
            opStr (str): The formula string to be modified.
            default_node (Node): The default node to be used for replacing variables.
            category (str): The category of the operation.
            scope (str): The scope of the operation.

        Returns:
            str: The modified formula string with all variables replaced by their corresponding values.
        """
        # Replace first all vars [] by value in result
        for m in re.finditer(self.VAR_EXPR, opStr):
            opStr = opStr.replace(m.group(0), str(self.replaceOneVarByValue(m.group(0), default_node, category, scope, position)))
        return opStr
    
    ## replaceFcnByVar
    def replaceFcnByVar(self, opStr, category, scope, position=0):
        """
        Replace all function placeholders in the formula with their corresponding values.

        Args:
            opStr (str): The formula string to be evaluated.
            category (str): The category of the operation.
            scope (str): The scope of the operation.

        Returns:
            str: The modified formula string.
        """
        while True:
            matches = list(re.finditer(self.FCN_EXPR, opStr))
            if not matches:
                break

            for match in matches:
                fcn_name, line_number = self._extract_function_name_and_line_number(match.group(0))
                attr = self._parse_function_name(fcn_name, category)
                opStr = self._process_function(opStr, attr, line_number, scope, match, position)

        return self._finalize_string(opStr)

    def _extract_function_name_and_line_number(self, fcn_str):
        fcn_name = fcn_str.strip("{}").strip()
        line_number = None
        if '!' in fcn_name:
            fcn_name, line_info = re.match(r'(.*?)!(\d+)', fcn_name).groups()
            line_number = int(line_info)
        return fcn_name, line_number

    def _parse_function_name(self, fcn_name, category):
        attr = fcn_name.split('.')
        if len(attr) == 1:
            attr.insert(0, category)
        elif len(attr) > 2:
            raise Exception("unknown function syntax for:", attr)
        return attr

    def _process_function(self, opStr, attr, line_number, scope, match, position=0):
        according_op = self.findOperation(attr[0], attr[1])
        if according_op is None:
            raise Exception("prb :", attr, match.group(0), attr[0], attr[1])

        related_nodes = findall(self.tree.root, lambda n: n.name.lower() == attr[0].lower())
        if not related_nodes:
            raise Exception("A problem is in :", attr, match.group(0))    

        for wks in related_nodes:                            
            accStr = self._replace_functions_with_values(according_op["operation"], attr, line_number)
            accStr = self.replaceAllVarsByValue(accStr, wks, attr[0], scope, position)
            opStr = opStr.replace(match.group(0), "("+ accStr+ ")")

        return opStr

    def _replace_functions_with_values(self, accStr, attr, line_number):
        for m in re.finditer(self.FCN_EXPR, accStr):
            rpl = m.group(0).strip("{}").strip()
            if line_number is not None:
                rpl = rpl + "!" + str(line_number)
            if len(rpl.split(".")) == 1:
                accStr = accStr.replace(m.group(0), "{"+attr[0]+"."+rpl+"}")
        return accStr

    def _finalize_string(self, opStr):
        try:
            return str(round(eval(opStr), self.FLOAT_PRECISION)) # Attention si l'user met rm -rf * par exemple !!
        except:
            return opStr
    
    def mapOperationValues(self, list_operations, category, scope):
        try:
            default_node = self.findNode(self.tree.root, category, scope, verbose=False)

            if default_node:                  
                operation_matrix = []                 
                
                for index, op in enumerate(list_operations):
                    if op["operation"] is None:
                        raise Exception("Operation can't be null :", op)
                    
                    # Create operations matrix
                    operation = {"operation_name": op["operation_name"], "formula" : op["operation"], "unit": op["unit"], "operations": []}
                    for position in range(self.tree.num_points):
                        opStr = self.replaceAllVarsByValue(op["operation"], default_node, category, scope, position)
                        operation["operations"].append(self.replaceFcnByVar(opStr, category, scope, position))
                        
                    operation["node_category"] = default_node
                    operation_matrix.append(operation)
                                                                    
                return operation_matrix
        except Exception as e:
            logger.error(e)
            raise e

        return None
        
    def operationParser(self):
        """
        Replace all Formula {} by Var [] while it's present in string of all operations 
        """
        for analyzer in self.tree.operation_sheets:
            for category, l_operations in analyzer.operations.items():
                if category is None or l_operations is None or not isinstance(category, str):
                    raise Exception('ReplaceFcnByVar needs category and operations')

                # Map values in self.operations
                for dst, stored_operations in self.operations.items():
                    values = self.mapOperationValues(l_operations, category, dst)

                    if values:
                        stored_operations.append(values)
    
        return stored_operations

    # Render functions
    def evaluate(self):
        """
        Replace all [] Expression by their Values to be evaluate next
        """
        
        # Search all {} operations and replace by []
        self.operationParser()

        # Eval all operations
        for dst, list_operations in self.operations.items():
            for operations in list_operations:
                for operation in operations:
                    try:
                        if operation["node_category"].analyzer.isSummarySheet():
                            operation["node_category"].analyzer.addSummary(operation["operation_name"], operation["operations"][0], operation["unit"])
                        elif operation["node_category"].analyzer.isCurvesSheet():
                            operation["node_category"].analyzer.addCurve(operation["operation_name"], operation["operations"], operation["unit"])
                    except Exception as e:
                        raise Exception("Error for evaluation of operations", operation, e)
