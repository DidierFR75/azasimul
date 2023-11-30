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
    
    def replaceOneVarByValue(self, word, default_node, category, scope):
        """
        Replace a variable in a formula with its corresponding value based on the category and scope of the operation.

        Args:
            word (str): The variable to be replaced in the formula.
            default_node (Node): The default node to be used for replacing variables.
            category (str): The category of the operation.
            scope (str): The scope of the operation.

        Returns:
            The corresponding value of the variable in the formula.
        """

        if word is None or category is None:
            raise Exception("replaceOneVarByValue needs all parameters to be filled.")

        correct_word = word.replace("[", "").replace("]", "")

        line_number = None
        # Check for "!" and extract line number 
        if '!' in correct_word:
            # Extract variable name and line number (if present)
            correct_word, line_info = re.match(r'(.*?)!(\d+)', correct_word).groups()
            line_number = int(line_info)

        attr = correct_word.split('.')

        if len(attr) == 1:
            attr.insert(0, category)

        if len(attr) > 1:
            node = self.findNode(self.tree.root, attr[0], scope)
        else:
            node = default_node

        # It is a constant
        if len(attr) == 3 and node.analyzer.isConstantSheet():
            constant = node.analyzer.getConstantByCategoryAndName(attr[1], attr[2])
            if constant is not None:
                return constant["value"]

            return None

        if node.analyzer.isSummarySheet():
            cw = attr[1].split('|')

            summary = node.analyzer.getSummaryByName(cw[0])

            if summary:
                if len(cw) == 2:
                    return self.convertFilter(summary["summary_value"], summary["unit"], cw[1])

                return summary["summary_value"]
            return None

        if node.analyzer.isCurvesSheet():
            spec = node.analyzer.getCurveByName(attr[1])

            if spec is not None:
                if spec["interpolation"] == "CONST":
                    return spec["values"][0]
                else:
                    try:
                        if line_number is not None and line_number <= len(spec["values"]):
                            val = spec["values"][line_number]
                        else:
                            val = spec["values"][0]
                    except:
                        raise Exception("Can't access data values ", spec)
                    return val
            else:
                raise Exception('Error: replaceOneVarByValue()', word, node, category, scope, attr, node.analyzer.curves)

        return None
    
    def replaceAllVarsByValue(self, opStr, default_node, category, scope):
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
            opStr = opStr.replace(m.group(0), str(self.replaceOneVarByValue(m.group(0), default_node, category, scope)))
        return opStr

    def replaceFcnByVar(self, opStr, category, scope):
        """
        Replace all function placeholders ({}) in the formula with their corresponding values ([]).

        Args:
            opStr (str): The formula string to be evaluated.
            category (str): The category of the operation.
            scope (str): The scope of the operation.

        Returns:
            str: The modified formula string with all function placeholders replaced by their evaluated values.
        """
        matches = re.finditer(self.FCN_EXPR, opStr)
        while matches is not None:
            for match in matches:
                according_op = None
                wks = None

                fcn_name = match.group(0).replace("{", "").replace("}", "").strip()
        
                line_number = None
                # Check for "!" and extract line number
                if '!' in fcn_name:
                    # Extract variable name and line number (if present)
                    fcn_name, line_info = re.match(r'(.*?)!(\d+)', fcn_name).groups()
                    line_number = int(line_info)
                
                attr = fcn_name.split('.')

                # if operation exist in list operation, add the value of it in it
                if len(attr) > 2:
                    raise Exception("unknown function syntax for:", attr)
            
                if len(attr) == 1:
                    attr.insert(0, category)
            
                according_op = self.findOperation(attr[0], attr[1])

                if according_op is not None:
                    related_nodes = findall(self.tree.root, lambda n: n.name.lower() == attr[0].lower())
                else:
                    raise Exception("prb :", attr, match.group(0), fcn_name)
            
                if according_op is not None and related_nodes != ():
                    for wks in related_nodes:                            
                        # Transform all {} in children by interpretable {}
                        accStr = according_op["operation"]
                        for m in re.finditer(self.FCN_EXPR, accStr):
                            rpl = m.group(0).replace("{", "").replace("}", "").strip()
                            if line_number is not None:
                                rpl = rpl+"!"+str(line_number)

                            if len(rpl.split(".")) == 1:
                                accStr = accStr.replace(m.group(0), "{"+attr[0]+"."+rpl+"}")

                        accStr = self.replaceAllVarsByValue(accStr, wks, attr[0], scope)
                    
                        opStr = opStr.replace(match.group(0), "("+ accStr+ ")")
                        try:
                            opStr = str(round(eval(opStr), 10))
                        except:
                            pass
                else:
                    raise Exception("A problem is in :", attr, match.group(0))    

            if re.search(self.FCN_EXPR, opStr) is not None:
                matches = re.finditer(self.FCN_EXPR, opStr)
            else:
                matches = None
        try:
            opStr = str(round(eval(opStr), 10))
        except:
            pass
        return opStr

    def mapOperationValues(self, list_operations, category, scope):
        try:
            default_node = self.findNode(self.tree.root, category, scope, verbose=False)

            if default_node:                  
                copy_operations = deepcopy(list_operations)    
                
                for index, op in enumerate(copy_operations):                            
                    if op["operation"] is None:
                        raise Exception("Operation can't be null :", op)
            
                    opStr = self.replaceAllVarsByValue(op["operation"], default_node, category, scope)
                    op["operation"] = self.replaceFcnByVar(opStr, category, scope)
                    
                    op["node_category"] = default_node

                    copy_operations[index] = op
                    
                return copy_operations
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
                            # Attention si l'user met rm -rf * par exemple !!
                            # logging.log(operation["operation"])
                            operation["operation"] = round(eval(str(operation["operation"])), 4)
                            # logging.log(operation["operation"])
                            if operation["node_category"].analyzer.isSummarySheet():
                                operation["node_category"].analyzer.addSummary(operation["operation_name"], operation["operation"], operation["unit"])
                            elif operation["node_category"].analyzer.isCurvesSheet():
                                operation["node_category"].analyzer.addCurve(operation["operation_name"], operation["operation"], operation["unit"], "CONST")
                        except Exception as e:
                            raise Exception("Error for evaluation of operations", operation, e)
