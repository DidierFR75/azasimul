from openpyxl import Workbook, load_workbook
from openpyxl.writer.excel import save_virtual_workbook
import os
import pandas as pd
import numpy as np
import scipy as sp
from scipy import interpolate
from datetime import datetime, timedelta
from pycel import ExcelCompiler
from dateutil.relativedelta import relativedelta
import re
from statistics import mean
from anytree import Node, RenderTree, find, Resolver, PostOrderIter

class InputAnalyzer:

    BASE_ELEMENTS_ROW = 17 # Location of base's elements
    UNIT_ROW = 18 # Location of units
    CURVE = 19 # Location of Curve's interpolations
    METADATA_COL = "A"
    POINT_N_COL = "B"
    DATE_COL = "D"
    PRODUCT_NAME = "Product-Type"
    PRODUCT_PARENT = "SubType"
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
    
    ### Helper's functions

    def isOperationSheet(self):
        if "operation" in self.sheet_name.lower():
            return True
        return False

    def isConstantSheet(self):
        if "constant" in self.sheet_name.lower():
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
                    result.append(float(interp1d(point["row"])))
                else:
                    result.append(list(filter(lambda v: v["row"] == point["row"], values))[0]["value"])
                    
        return result

    # Access Functions

    def addSpecification(self, specifcation_name, value, unit, interpolation="CONST"):
        """
        Add new Specification to the analyzer, if specification exists we do nothing
        """

        if self.getSpecificationByName(specifcation_name) is not None:
            print(specifcation_name)
            return None

        next_free_column = self.specifications[-1]["column"]+1

        self.specifications.append({
            "column": next_free_column,
            "specification_name": specifcation_name,
            "values": [value] * len(self.points), # 
            "unit": unit,
            "interpolation": interpolation
        })

    def getRawDataStorage(self):
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

        # Get all elements in worksheet
        self.metadatas = self._generateMetaData()
        self.points = self._generatePointsWithDates()
        self.specifications = self._generateSpecifications()
        
        if((self.points != [] or self.specifications != []) and self.metadatas == {}):
            raise Exception("Metadatas are missing...{}".format(self.sheet_name))

        # Add Interpolate values  
        for specification in self.specifications:
            specification["values"] = self._evaluateInterpolation(specification)       
        
        return True
        
    def getSpecificationByName(self, name):
        return next((item for item in self.specifications if item["specification_name"].lower() == name.lower()), None)

    def getConstantByName(self, name):
        test = iter([item for item in list(self.constants.values())[0] if item["constant_name"].lower() == name.lower()])
        return next(test, None)

    def getOperationByName(self, name):
        return next((item for item in self.operations if item["operation_name"].lower() == name.lower()), None)                         

class SheetTree:
    def __init__(self, path) -> None:
        self.path = path
        self.root = Node("root")
        self.all_sheet = None
        self.operation_sheets = []
    
    def analyzeAllSheet(self):
        result = {}
        all_files = next(os.walk(self.path), (None, None, []))[2]
        all_wks = {file: load_workbook(self.path + file) for file in all_files}

        for file, wb in all_wks.items():
            result[file] = []
            for sheet_name in all_wks[file].sheetnames:
                analyzer = InputAnalyzer(wb[sheet_name], sheet_name, self.path + file)
                if analyzer.getRawDataStorage():
                    result[file].append({sheet_name: analyzer})

        return result

    def mapSheetToTree(self):
        liste = []
        self.all_sheet = self.analyzeAllSheet()
       
        # Create all nodes
        for file in self.all_sheet:
            for sheet in self.all_sheet[file]:
                for sheet_name, analyzer in sheet.items():
                    if analyzer.isOperationSheet():
                        self.operation_sheets.append(analyzer)
                        continue
                
                    if analyzer.isConstantSheet():
                        self.root.analyzer = analyzer
                        self.root.name = "Constants"
                        continue

                    if analyzer.metadatas == {}:
                        continue

                    parent_name = analyzer.metadatas[analyzer.PRODUCT_PARENT] if (analyzer.PRODUCT_PARENT in analyzer.metadatas) else None
                                                
                    liste.append(
                        (parent_name,
                        analyzer.metadatas[analyzer.PRODUCT_NAME],
                        Node(analyzer.metadatas[analyzer.PRODUCT_NAME], analyzer=analyzer))
                    )
        
        # Add parent for all nodes
        for element in liste:
            if element[0] is None:
                element[2].parent = self.root
            else:
                i = [i for i, v in enumerate(liste) if v[1] == element[0]]
                if i != []:
                    element[2].parent = liste[i[0]][2]

class SheetInterpreter:
    """
    Convert all operations with specific language to comprehensible mathematical operation in analyzer
    """
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

    def replaceVarByValue(self, word, node):
        """
        Replace Word by his Variable Value in the according worksheet
        """

        correct_word = word.replace("[", "").replace("]", "")
        attr = correct_word.split('.')
    
        if len(attr) == 2:
            if find(self.tree.root, lambda node: node.name.lower() == attr[0].lower()) is None:
                raise Exception("The sheet "+ attr[0]+ " doesn't map in the tree...")
            correct_word = attr[1]

        spec = node.analyzer.getSpecificationByName(correct_word)
        
        # if value not define, search in child and sum all of "word" values
        if spec is None:
            val = 0
            for child in node.children:
                val = val + self.replaceVarByValue(word, child)
            return val
        
        if spec is not None:
            if spec["interpolation"] == "CONST":
                val = spec["values"][0]
            else:
                # make an average of each interpolate's values 
                val = mean(spec["values"])
        return val

    def replaceFcnByVar(self, operations, operation_category):
        """
        Replace all {} by [] while it's present in string of all operations 
        """
        expression_fcn = '\{[\(\) \.a-zA-Z0-9]+\}'
        expression_var = '\[[ \(\)a-zA-Z0-9\.]+\]'

        if operation_category is None or operations is None:
            raise Exception('ReplaceFcnByVar needs operation_category and operations')
        
        origin_wks = find(self.tree.root, lambda node: node.name.lower() == operation_category.lower())
        if origin_wks is not None:
            
            for operation in operations:
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

    def _evaluateOperationValues(self):
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
                        try:
                            operation["operation"] = eval(operation["operation"])
                        except:
                            pass
    
    def _addOperationValueToAnalyzer(self):
        """
        Add all evaluate values to analyzer class as new column with CONST Value
        """
        for o_wks in self.tree.operation_sheets:
            for operation_category, operations in o_wks.operations.items():
                wks = find(self.tree.root, lambda node: node.name.lower() == operation_category.lower())
                if wks is not None:
                    for operation in operations:
                        wks.analyzer.addSpecification(operation["operation_name"], operation["operation"], operation["unit"], "CONST")
    
    # Access functions
    def evaluate(self):
        self._evaluateOperationValues()
        self._addOperationValueToAnalyzer()

class OutputAnalyzer:

    EXPRESSION = '\[[ \(\)a-zA-Z0-9\.]+\]' # expression of a var in output's cell

    def __init__(self, wb, sheet_name, path, tree) -> None:
        self.evaluator = ExcelCompiler(filename=path)
        self.sheet_name = sheet_name
        self.wb = wb
        self.ws = self.wb[sheet_name]
        self.tree = tree

    def isInterpretable(self, value):
        if value is None or not isinstance(value, str) or value == "" or value == " " or value == "$":
            return False

        if re.search(value, self.EXPRESSION):
            return True
            
        return False

    def findAndReplaceAnnotateValues(self):
        """
        Find and replace all annotate's values by their specification's value
        """
        for row in self.ws:
            for cell in row:
                if self.isInterpretable(cell.value):
                    matches = re.finditer(self.EXPRESSION, cell.value)
                    for match in matches:
                        m = match.group(0).replace("[", "").replace("]", "").strip()
                        attr = m.split(".")
                        if len(attr) > 1:
                            node = find(self.tree.root, lambda node: node.name.lower() == attr[0].lower())
                            if node is not None:
                                val = {}

                                if node.analyzer.isSpecificationSheet():
                                    val = node.analyzer.getSpecificationByName(attr[1])
                                    if val:
                                        if val["interpolation"] == "CONST":
                                            val = val["values"][0]
                                        else:
                                            val = mean(val["values"])
                                
                                if node.analyzer.isConstantSheet():
                                    val = node.analyzer.getConstantByName(attr[1])
                                
                                cell.value = val["value"] if "value" in val and val["value"] is not None else ""

    def save(self, path):
        self.wb.save(path)

class SheetOutputGenerator:

    def __init__(self, input_path, output_path) -> None:
        self.output_path = os.getcwd() + output_path
        tree_interpreter = SheetInterpreter(os.getcwd()+ "/simulator"+input_path)
        tree_interpreter.evaluate()
        self.tree = tree_interpreter.tree

    def analyzeAllOutputSheet(self):
        result = {}
        all_files = next(os.walk(self.output_path), (None, None, []))[2]
        all_wks = {file: load_workbook(self.output_path + file) for file in all_files}

        for file, wb in all_wks.items():
            result[file] = {sheet_name: OutputAnalyzer(wb, sheet_name, self.output_path + file, self.tree) for sheet_name in all_wks[file].sheetnames}
            
        return result

    def generate(self, to):
        """
        Generate final output xlsx
        """
        all_sheets = self.analyzeAllOutputSheet()
        count = 0
        for file, sheets in all_sheets.items():
            count +=1
            for sheet_name, analyzer in sheets.items():
                analyzer.findAndReplaceAnnotateValues()
                analyzer.save(to+"_"+str(count)+".xlsx")