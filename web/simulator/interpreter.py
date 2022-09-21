from curses import keyname
from unicodedata import category
from openpyxl import Workbook, load_workbook
from openpyxl.writer.excel import save_virtual_workbook
import os
import pandas as pd
import numpy as np
import scipy as sp
from scipy import interpolate
from datetime import date, datetime, timedelta
from pycel import ExcelCompiler
from dateutil.relativedelta import relativedelta
import re
from statistics import mean
from anytree import Node, RenderTree, find, Resolver, PostOrderIter
import pathlib
import zipfile
import math
import datetime
from copy import copy

class InputAnalyzer:

    BASE_ELEMENTS_ROW = 17 # Location of base's elements
    UNIT_ROW = 18 # Location of units
    CURVE = 19 # Location of Curve's interpolations
    METADATA_COL = "A"
    POINT_N_COL = "B"
    DATE_COL = "D"
    PRODUCT_NAME = "Product-Type"
    PRODUCT_PARENT = "SubType"
    CATEGORY = "Category"
    DELIMITER_SHEET_UNFOLLOW = "_"

    def __init__(self, ws, sheet_name, path) -> None:
        self.evaluator = ExcelCompiler(filename=path)
        self.sheet_name = sheet_name
        self.ws = ws

        self.specifications = []
        self.points = []
        self.metadatas = {}
        self.operations = {}
        self.constants = {}
        self.summary = []

    # Carefull _getValuesBySpecificiation could return bad values for % as exemple
    # Get external parameters
    
    ### Util's functions

    def log_interp1d(self, xx, yy, kind='linear'):
        """
        Return the log interpolation on 1 dimension
        """
        logx = np.log10(xx)
        logy = np.log10(yy)
        lin_interp = interpolate.interp1d(logx, logy, kind=kind, fill_value="extrapolate")
        log_interp = lambda zz: np.power(10.0, lin_interp(np.log10(zz)))
        return log_interp

    def evaluate(self, cell):
        """
        Return the evaluation's value of a given cell (rounded by 3)
        """
        eval = self.evaluator.evaluate(self.sheet_name+"!"+cell.coordinate)
        if isinstance(eval, float):
            eval = round(eval, 3)
        return eval
    
    ### Test type's functions

    def isOperationSheet(self):
        if "operation" in self.sheet_name.lower():
            return True
        return False

    def isConstantSheet(self):
        if "constant" in self.sheet_name.lower():
            return True
        return False
    
    def isSummarySheet(self):
        if "summary" in self.sheet_name.lower():
            return True
        return False

    def isSpecificationSheet(self):
        if self.specifications != [] and self.points != []:
            return True
        return False

    # Generator's functions

    def _generatePointsWithDates(self):
        """
            Return dict (row_number, point_no, date) of all points and associate's date
        """
        points=[]
        for point in self.ws[self.POINT_N_COL]:
            if point.value is not None and (type(point.value) is int or type(point.value) is float or (type(point.value) is str and point.value.startswith("=")) ):
                points.append({
                    "row": point.row, 
                    "point_n": self.evaluate(point), 
                    "date": self.ws[self.DATE_COL+str(point.row)].value
                })
        
        return self._fullFillPointsWithDates(points)

    def _generateSpecifications(self):
        """
        Return a sorted (by ASC) dict (column, specification, unit, interpolation) at BASE_ELEMENTS_ROW for a given sheetname
        Ignore the firsts 2 elements because they always not belong to specifications
        """
        return sorted([{
            "column": be.column, 
            "specification_name": be.value,
            "values": None,
            "unit": self.ws.cell(row=self.UNIT_ROW, column=be.column).value, 
            "interpolation": self.ws.cell(row=self.CURVE, column=be.column).value
        } for be in self.ws[self.BASE_ELEMENTS_ROW] if be.value is not None][2:], key=lambda x: x["column"])

    def _generateMetaData(self):
        """
        Return array of tuples (row_id, metadata_name, metadata_value) for a given sheetname
        """
        return {cell.value: self.ws['B'][cell.row-1].value 
            for cell in self.ws[self.METADATA_COL] 
            if (cell.value is not None and self.ws['B'][cell.row-1].value is not None and cell.row < self.BASE_ELEMENTS_ROW)}

    def _generateConstants(self):
        """
        Return all global constant in the sheet
        """
        compositions = [(cmp.row, cmp.value) for cmp in self.ws["A"] if cmp.value is not None]

        result = {}
        for index, cmp in enumerate(compositions):
            tmp = []            
            if(index != len(compositions)-1):
                last_row = compositions[index+1][0]-1
            else:
                last_row = len(self.ws["B"])

            for x in range(cmp[0]+1, last_row):
                if self.ws["B"+str(x)].value is not None:
                    tmp.append({
                        "constant_name": self.ws["B"+str(x)].value,
                        "value": self.evaluate(self.ws["C"+str(x)]),
                        "unit": self.evaluate(self.ws["D"+str(x)])
                    })
            
            result[cmp[1]] = tmp

        return result

    def _generateSummary(self):
        for composition in self.ws["A"]:
            if composition.value is not None and self.ws.cell(row=composition.row, column=composition.column+1).value is not None:
                self.addSummary(composition.value, self.ws.cell(row=composition.row, column=composition.column+1).value, self.ws.cell(row=composition.row, column=composition.column+2).value)

    def _generateOperations(self):
        """
        Return operations
        """
        items = [(it.row, it.value) for it in self.ws["A"] if it.value is not None]

        result = {}
        for index, fcn in enumerate(items):
            tmp = []            
            if(index != len(items)-1):
                last_row = items[index+1][0]-1
            else:
                last_row = len(self.ws["B"])

            for x in range(fcn[0]+1, last_row):
                if self.ws["B"+str(x)].value is not None:
                    tmp.append({
                        "operation_name": self.ws["B"+str(x)].value,
                        "operation": self.evaluate(self.ws["C"+str(x)]),
                        "unit": self.ws["D"+str(x)].value
                    })
            
            result[fcn[1]] = tmp

        return result

    def _fullFillPointsWithDates(self, points):
        """
            Return a fullfill array of points associate with dates 
        """
        ref_date = None
        for index, point in enumerate(points):
            if point["date"] is not None:
                ref_date = {"index": index, "date": point["date"]}
                break
        
        if ref_date is not None:
            for index, point in enumerate(points):
                if point["date"] is None:
                    if index < ref_date["index"]:
                        point["date"] = ref_date["date"] + relativedelta(years=-(ref_date["index"]-index))
                    else:
                        point["date"] = ref_date["date"] + relativedelta(years=(index-ref_date["index"]))
        
        return points
     
    def _getValuesBySpecificiation(self, specification):
        result = []
        value = None
        for point in self.points:
            cell = self.ws.cell(row=point["row"], column=specification["column"])
            if cell.value is not None and cell.value != "#REF!":
                if isinstance(cell.value, str):
                    if cell.value.startswith("="):
                        value = self.evaluator.evaluate(self.sheet_name+"!"+cell.coordinate)
                    if "%" in cell.value:
                        value = float(cell.value.replace("%", ""))/100
                elif isinstance(cell.value, float) or isinstance(cell.value, int):
                    value = cell.value
                result.append({
                    "row": point["row"],
                    "value": value
                })
        return result 

    def _evaluateInterpolation(self, specification):
        result = []
        values = self._getValuesBySpecificiation(specification)
        
        if (specification["interpolation"] == "CONST" and len(values) > 0) or (specification["interpolation"] is None and len(values) == 1):
            return [next(item["value"] for item in values if item["value"] is not None)] * len(self.points)
        elif len(values) >= 2:
            # Linear Interpolation by default
            interp1d = interpolate.interp1d([v["row"] for v in values], [v["value"] for v in values], fill_value="extrapolate")
            
            # Log interpolation
            if specification["interpolation"] == "LOG":
                interp1d = self.log_interp1d([v["row"] for v in values], [v["value"] for v in values])

            # Add result of interpolation for each point
            for point in self.points:
                if not any(v["row"] == point["row"] for v in values):
                    result.append(round(float(interp1d(point["row"])), 3))
                else:
                    result.append(list(filter(lambda v: v["row"] == point["row"], values))[0]["value"])
                    
        return result

    # Init Functions

    def create(self):
        """
            Return JSON storage of the input
        """

        if self.sheet_name.startswith(self.DELIMITER_SHEET_UNFOLLOW):
            return False

        if self.isOperationSheet():
            self.operations = self._generateOperations()
            return True

        if self.isConstantSheet():
            self.constants = self._generateConstants()
            return True

        if self.isSummarySheet():
            self._generateSummary()
            return True

        # Get all elements in worksheet
        self.metadatas = self._generateMetaData()
        self.points = self._generatePointsWithDates()
        self.specifications = self._generateSpecifications()
        
        if self.isSpecificationSheet() and self.metadatas == {}:
            raise Exception("Metadatas are missing...{}".format(self.sheet_name))

        # Add Interpolate values  
        for specification in self.specifications:
            specification["values"] = self._evaluateInterpolation(specification)       
        
        return True
    
    # Add Functions

    def addSpecification(self, specifcation_name, value, unit, interpolation="CONST"):
        """
        Add new Specification to the analyzer, if specification exists we do nothing
        """

        if self.getSpecificationByName(specifcation_name) is not None:
            return None

        next_free_column = self.specifications[-1]["column"]+1

        self.specifications.append({
            "column": next_free_column,
            "specification_name": specifcation_name,
            "values": [value] * len(self.points), 
            "unit": unit,
            "interpolation": interpolation
        })
    
    def addSummary(self, summary_name, value, unit):
        if self.getSummaryByName(summary_name) is not None:
            return None

        self.summary.append({
            "summary_name": summary_name,
            "summary_value": value,
            "unit": unit
        })

    # Access Functions

    def getSpecificationByName(self, name):
        return next((item for item in self.specifications if item["specification_name"].lower() == name.lower()), None)

    def getConstantByName(self, name):
        result = iter([item for item in list(self.constants.values())[0] if item["constant_name"].lower() == name.lower()])
        return next(result, None)
    
    def getConstantByCategoryAndName(self, category, name):
        if category in self.constants:
            result = iter([item for item in self.constants[category] if item["constant_name"].lower() == name.lower()])
            return next(result, None)

    def getSummaryByName(self, name):
        result = iter([item for item in self.summary if item["summary_name"].lower() == name.lower()])
        return next(result, None)

    def getOperationByName(self, name):
        result = iter([item for item in self.operations if item["operation_name"].lower() == name.lower()])
        return next(result, None)                        

    def getCategory(self):
        if self.CATEGORY in self.metadatas:
            return str(self.metadatas[self.CATEGORY])
        return None

class SheetTree:
    def __init__(self, path) -> None:
        self.path = path
        
        self.root = Node("root")
        self.root.name = "Summary"
        self.root.categories = {}

        self.all_sheet = None
        self.operation_sheets = []

    def analyzeAllSheet(self, path):
        """
        Return dict with {file: {sheetname: analyzer}}
        """
        result = {}

        # Load all workbooks
        all_files = next(os.walk(path), (None, None, []))[2]
        all_wks = {file: load_workbook(path + file) for file in all_files}
        
        # Create dict with file: {sheetname: analyzer}
        for file, wb in all_wks.items():
            result[file] = []
            for sheet_name in all_wks[file].sheetnames:
                analyzer = InputAnalyzer(wb[sheet_name], sheet_name, path + file)
                if analyzer.create():
                    result[file].append({sheet_name: analyzer})

        return result

    def mapSheetToTree(self, path=None):
        """
        Add sheets in path to the tree, path not define default self.path sheet are add else it's personalize sheet's path
        """
        liste = []

        self.all_sheet = self.analyzeAllSheet(path if path is not None else self.path)
       
        # Create all nodes
        for file in self.all_sheet:
            for sheet in self.all_sheet[file]:
                for sheet_name, analyzer in sheet.items():
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
                    
                    # Get parent name if exist
                    parent_name = analyzer.metadatas[analyzer.PRODUCT_PARENT] if (analyzer.PRODUCT_PARENT in analyzer.metadatas) else None
                        
                    node = Node(analyzer.metadatas[analyzer.PRODUCT_NAME], analyzer=analyzer)
                    
                    # Get and add category to self.root.categories if exist
                    category = analyzer.getCategory()
                    if category is not None:
                        self.root.categories[category.lower()] = category.upper()+":"
                        node.category = category.lower()
                                                
                    liste.append(
                        (parent_name,
                        analyzer.metadatas[analyzer.PRODUCT_NAME],
                        node
                    ))
        
        # Add parent for all nodes
        for element in liste:
            # if no parent
            if element[0] is None:
                element[2].parent = self.root
            else:
                i = [i for i, v in enumerate(liste) if v[1] == element[0] and element[2].category == v[2].category]
                if i != []:
                    element[2].parent = liste[i[0]][2]

class SheetInterpreter:

    FILTERS_DISPATCH = {"date" : {
            "year" : lambda x: x.year,
            "month": lambda x: x.month,
            "day": lambda x: x.day
    }}

    def __init__(self, folder) -> None:
        self.tree = SheetTree(folder)
        self.tree.mapSheetToTree()

    # Helper functions
    def findOperation(self, operation_category, operation_name):
        """
        Find an operation by it category and it operation_name 
        """
        for analyzer in self.tree.operation_sheets:
            for analyzer_operation_category, operations in analyzer.operations.items():
                if analyzer_operation_category.lower() == operation_category.lower():
                    return next((operation for operation in operations if operation["operation_name"].lower() == operation_name.lower()), None) 
        return None

    def convertFilter(self, value, unit, filter):
        """
        Convert value by it filter
        Ex : 01/01/2022|year = 2022
        """
        if unit.lower() in self.FILTERS_DISPATCH and filter.lower() in self.FILTERS_DISPATCH[unit]:
            return self.FILTERS_DISPATCH[unit.lower()][filter.lower()](value)
        return value

    def replaceVarByValue(self, word, node):
        """
        Replace Word by his Variable Value in the according worksheet
        """

        correct_word = word.replace("[", "").replace("]", "")
        attr = correct_word.split('.')
    
        if len(attr) == 2:
            if find(self.tree.root, lambda node: node.name.lower() == attr[0].lower()) is None:
                raise Exception("The sheet "+ attr[0]+ " doesn't map in the tree...")

        if node.analyzer.isSummarySheet():
            cw = attr[1].split('|')

            summary = node.analyzer.getSummaryByName(cw[0])

            if summary is not None and summary != {}:
                if len(cw) == 2:
                    return self.convertFilter(summary["summary_value"], summary["unit"], cw[1])
                    
                return summary["summary_value"]
            return None

        if node.analyzer.isSpecificationSheet():
            spec = node.analyzer.getSpecificationByName(correct_word)
            
            # if value not define, search in child and sum all of "word" values
            if spec is None:
                val = 0
                for child in node.children:
                    val = val + self.replaceVarByValue(word, child)
                return val
            
            if spec is not None:
                if spec["interpolation"] == "CONST":
                    return spec["values"][0]
                else:
                    # make an average of each interpolate's values 
                    return mean(spec["values"])
        
        return None

    def replaceFcnByVar(self, operations, operation_category):
        """
        Replace all {} by [] while it's present in string of all operations 
        """
        expression_fcn = '\{[\(\) \.a-zA-Z0-9]+\}'
        expression_var = '\[[ \(\)\|\+a-zA-Z0-9\.]+\]'

        if operation_category is None or operations is None:
            raise Exception('ReplaceFcnByVar needs operation_category and operations')
        
        origin_wks = find(self.tree.root, lambda node: node.name.lower() == operation_category.lower())
        if origin_wks is not None:
            for operation in operations:
                if operation["operation"] is None:
                    continue

                matches = re.finditer(expression_fcn, operation["operation"])

                # Replace first all vars [] by value
                for m in re.finditer(expression_var, operation["operation"]):
                    operation["operation"] = operation["operation"].replace(m.group(0), str(self.replaceVarByValue(m.group(0), origin_wks)))

                # Replace all fcn {} by value
                while matches is not None:
                    for match in matches:
                        according_op = None
                        wks = None

                        fcn_name = match.group(0).replace("{", "").replace("}", "").strip()
                        attr = fcn_name.split('.')

                        # if operation exist in list operation, add the value of it in it
                        if len(attr) == 1:
                            according_op = next((op for op in operations if op["operation_name"] == fcn_name), None)
                            if according_op is not None:
                                wks = find(self.tree.root, lambda node: node.name.lower() == operation_category.lower())
                            
                        # Check if fcn_name is a child or parent function
                        if len(attr) == 2:
                            for analyzer in self.tree.operation_sheets:
                                according_op = self.findOperation(attr[0], attr[1])
                            
                            if according_op is not None:
                                wks = find(self.tree.root, lambda node: node.name.lower() == attr[0].lower())                        
                            
                        if according_op is not None and wks is not None:                            
                            # Transform all {} in children by interpretable {}
                            for m in re.finditer(expression_fcn, according_op["operation"]):
                                rpl = m.group(0).replace("{", "").replace("}", "").strip()

                                if len(rpl.split(".")) == 1:
                                    according_op["operation"] = according_op["operation"].replace(m.group(0), "{"+attr[0]+"."+rpl+"}")

                            # Transform all [] by value to avoid legacy interpretation problems
                            for m in re.finditer(expression_var, according_op["operation"]):
                                according_op["operation"] = according_op["operation"].replace(m.group(0), str(self.replaceVarByValue(m.group(0), wks)))

                            operation["operation"] = operation["operation"].replace(match.group(0), "("+according_op["operation"]+")")
                            
                    if re.search(expression_fcn, operation["operation"]) is not None:
                        matches = re.finditer(expression_fcn, operation["operation"])
                    else:
                        matches = None
                
        return operations

    def evaluate(self):
        """
        Replace all [] Expression by their Values to be evaluate next
        """
        
        # Search all {} operations and replace by []
        for o_wks in self.tree.operation_sheets:
            for operation_category, operations in o_wks.operations.items():
                wks = find(self.tree.root, lambda node: node.name.lower() == operation_category.lower())
                if wks is not None:
                    operations = self.replaceFcnByVar(operations, operation_category)
        
        # Eval all operations
        for o_wks in self.tree.operation_sheets:
            for operation_category, operations in o_wks.operations.items():
                wks = find(self.tree.root, lambda node: node.name.lower() == operation_category.lower())
                if wks is not None:
                    for operation in operations:
                        if operation["operation"] is None:
                            continue
                        try:
                            # Attention si l'user met rm -rf * par exemple !!
                            operation["operation"] = eval(operation["operation"])
                            if wks.analyzer.isSummarySheet():
                                wks.analyzer.addSummary(operation["operation_name"], operation["operation"], operation["unit"])
                            if wks.analyzer.isSpecificationSheet():
                                wks.analyzer.addSpecification(operation["operation_name"], operation["operation"], operation["unit"], "CONST")
                        except:
                            pass                        

class OutputAnalyzer:

    EXPRESSION = '\[[ \(\)\|\+a-zA-Z0-9\.]+\]' # expression of a var in output's cell
    FUNCTION = {
        "for": "FOR:",
    }

    FILTERS_DISPATCH = {
        "category": {}
    }

    def __init__(self, wb, sheet_name, path, tree) -> None:
        self.evaluator = ExcelCompiler(filename=path)
        self.sheet_name = sheet_name
        self.wb = wb
        self.ws = self.wb[sheet_name]
        self.tree = tree
        self.FILTERS_DISPATCH["category"] = {item: lambda x: x for item in self.tree.root.categories}

    def convertFilter(self, value, unit, filter):
        """
        Convert value by it filter
        Ex : 01/01/2022|year = 2022
        """
        if unit.lower() in self.FILTERS_DISPATCH and filter.lower() in self.FILTERS_DISPATCH[unit]:
            return self.FILTERS_DISPATCH[unit.lower()][filter.lower()](value)
        return value

    def copyCellStyle(self, cell, new_cell):
        """
        Return new_cell with the style of cell
        """
        if cell.has_style:
            new_cell.font = copy(cell.font)
            new_cell.border = copy(cell.border)
            new_cell.fill = copy(cell.fill)
            new_cell.number_format = copy(cell.number_format)
            new_cell.protection = copy(cell.protection)
            new_cell.alignment = copy(cell.alignment)
        return new_cell

    def isInterpretable(self, value):
        if value is None or not isinstance(value, str) or value == "" or value == " " or value == "$":
            return False
        
        # Check if value start with one value of self.FUNCTION
        valid_func = next(iter([True for key_func, value_func in self.FUNCTION.items() if value.startswith(value_func)]), False)

        if re.search(value, self.EXPRESSION) or valid_func:
            return True
            
        return False

    def getSpecificationByCategoryAndName(self, category_name, name):
        pass
    
    def findAndReplaceAnnotateValues(self):
        """
        Find and replace all annotate's values by their specification's value
        """
        for row in self.ws:
            for_expression = False
            for cell in row:
                # add new row if not already did
                if self.isInterpretable(cell.value):                        
                    matches = re.finditer(self.EXPRESSION, cell.value)
                    for match in matches:
                        node = None
                        m = match.group(0).replace("[", "").replace("]", "").strip()
                        attr = m.split(".")
                        if len(attr) > 1:
                            filter = attr[1].split("|")
                            attr[1] = filter[0]
                            if len(filter) > 1:
                                node = find(self.tree.root, lambda node: node.name.lower() == attr[0].lower() and node.category.lower() == filter[1].lower())
                            else:
                                node = find(self.tree.root, lambda node: node.name.lower() == attr[0].lower())

                            if node is not None:
                                data = None
                                val = {}

                                if node.analyzer.isSpecificationSheet():
                                    data = node.analyzer.getSpecificationByName(attr[1])
                                    if data is not None:
                                        if data["interpolation"] == "CONST":
                                            val = data["values"][0]
                                        else:
                                            val = mean(data["values"])

                                        if cell.value.startswith(self.FUNCTION["for"]):
                                            nb_points = len(node.analyzer.points)
                                            if not for_expression:
                                                for_expression = True
                                                for i in range(1, nb_points+1):
                                                    self.ws.insert_rows(cell.row+i)

                                            for i in range(1, nb_points+1):
                                                self.ws.cell(row=cell.row+i, column=cell.column).value = data["values"][i-1]
                                                self.copyCellStyle(cell, self.ws.cell(row=cell.row+i, column=cell.column))

                                if node.analyzer.isConstantSheet():
                                    if len(attr) > 2:
                                        data = node.analyzer.getConstantByCategoryAndName(attr[1], attr[2])
                                        val = data["value"]
                                
                                if node.analyzer.isSummarySheet():
                                    data = node.analyzer.getSummaryByName(attr[1])
                                    val = data["summary_value"] if data is not None else None

                                cell.value = val if val != {} and val is not None else ""

    def save(self, path):
        self.wb.save(path)

class SheetOutputGenerator:

    def __init__(self, input_path, output_path) -> None:
        self.output_path = output_path
        tree_interpreter = SheetInterpreter(input_path)
        tree_interpreter.evaluate()
        self.tree = tree_interpreter.tree

    def analyzeAllOutputSheet(self):
        """
        Return dict with file: {sheetname: analyzer} 
        """
        result = {}
        
        # Load all workbooks
        all_files = next(os.walk(self.output_path), (None, None, []))[2]
        all_wks = {file: load_workbook(self.output_path + file) for file in all_files}
        
        # Create dict with file: {sheetname: analyzer}
        for file, wb in all_wks.items():
            result[file] = {sheet_name: OutputAnalyzer(wb, sheet_name, self.output_path + file, self.tree) for sheet_name in all_wks[file].sheetnames}
            
        return result

    def _createZip(self, to, name):
        """
        Create zip of a folder and return name.zip path
        """
        directory = pathlib.Path(to)
        destination = str(directory.parent.absolute())+"/"+name+".zip"

        with zipfile.ZipFile(destination, mode="w") as archive:
            for file_path in directory.iterdir():
                archive.write(file_path, arcname=file_path.name)
        return destination

    def generate(self, folder, name):
        """
        Generate final output xlsx
        """
        all_sheets = self.analyzeAllOutputSheet()

        # Create folder is not exist
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Replace var in output model folder by values and return a zip file of all of them
        count = 0
        for file, sheets in all_sheets.items():
            count +=1
            for sheet_name, analyzer in sheets.items():
                analyzer.findAndReplaceAnnotateValues()
                analyzer.save(folder+"simulation_"+str(count)+".xlsx")

        return self._createZip(folder, name)

class FileChecker:
    def __init__(self, path) -> None:
        self.path = path
        self.summary = None
        self.non_accepted = []

    def checkForSpecFormat(self):
        # Check if file contains only specifications and track summary data as well ass non accepted files as Constants or Operations
        wb = load_workbook(self.path)
        for sheet_name in wb.sheetnames:
            analyzer = InputAnalyzer(wb[sheet_name], sheet_name, self.path)
            if analyzer.create():
                if analyzer.isSummarySheet():
                    self.summary = analyzer.summary
                    wb.remove(wb[sheet_name])
                
                if analyzer.isConstantSheet() or analyzer.isOperationSheet():
                    self.non_accepted.append(sheet_name)
                    wb.remove(wb[sheet_name])
                        
        wb.save(self.path)
