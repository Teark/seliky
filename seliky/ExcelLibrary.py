import os
import natsort
from operator import itemgetter
from datetime import datetime, timedelta
from xlrd import open_workbook, cellname, xldate_as_tuple, \
    XL_CELL_NUMBER, XL_CELL_DATE, XL_CELL_TEXT, XL_CELL_BOOLEAN, \
    XL_CELL_ERROR, XL_CELL_BLANK, XL_CELL_EMPTY, error_text_from_code
from xlwt import easyxf, Workbook
from xlutils.copy import copy as copy


class ExcelLibrary:
    """
    This test library provides keywords to allow opening, reading, writing
     and saving Excel files from Robot Framework.


    *Before running tests*

    Prior to running tests, ExcelLibrary must first be imported into your Robot test suite.

    Example:
        | Library | ExcelLibrary |

    """

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        self.wb = None
        self.tb = None
        self.sheetNum = None
        self.sheetNames = None
        self.fileName = None
        if os.name is "nt":
            self.tmpDir = "Temp"
        else:
            self.tmpDir = "tmp"

    def open_excel(self, filename, useTempDir=False):
        """
        Opens the Excel file from the path provided in the file name parameter.
        If the boolean useTempDir is set to true, depending on the operating system of the computer running the test the file will be opened in the Temp directory if the operating system is Windows or tmp directory if it is not.

        Arguments:
                |  File Name (string)                      | The file name string value that will be used to open the excel file to perform tests upon.                                  |
                |  Use Temporary Directory (default=False) | The file will not open in a temporary directory by default. To activate and open the file in a temporary directory, pass 'True' in the variable. |
        Example:

        | *Keywords*           |  *Parameters*                                      |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |

        """
        if useTempDir is True:
            print('Opening file at %s' % filename)
            self.wb = open_workbook(os.path.join("/", self.tmpDir, filename), formatting_info=True, on_demand=True)
        else:
            self.wb = open_workbook(filename, formatting_info=True, on_demand=True)
        self.fileName = filename
        self.sheetNames = self.wb.sheet_names()

    def open_excel_current_directory(self, filename):
        """
        Opens the Excel file from the current directory using the directory the test has been run from.

        Arguments:
                |  File Name (string)  | The file name string value that will be used to open the excel file to perform tests upon.  |
        Example:

        | *Keywords*           |  *Parameters*        |
        | Open Excel           |  ExcelRobotTest.xls  |

        """
        workdir = os.getcwd()
        print('Opening file at %s' % filename)
        self.wb = open_workbook(os.path.join(workdir, filename), formatting_info=True, on_demand=True)
        self.sheetNames = self.wb.sheet_names()

    def get_sheet_names(self):
        """
        Returns the names of all the worksheets in the current workbook.

        Example:

        | *Keywords*              |  *Parameters*                                      |
        | Open Excel              |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Get Sheets Names        |                                                    |

        """
        sheetNames = self.wb.sheet_names()
        return sheetNames

    def get_number_of_sheets(self):
        """
        Returns the number of worksheets in the current workbook.

        Example:

        | *Keywords*              |  *Parameters*                                      |
        | Open Excel              |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Get Number of Sheets    |                                                    |

        """
        sheetNum = self.wb.nsheets
        return sheetNum

    def get_column_count(self, sheetname):
        """
        Returns the specific number of columns of the sheet name specified.

        Arguments:
                |  Sheet Name (string)  | The selected sheet that the column count will be returned from. |
        Example:

        | *Keywords*          |  *Parameters*                                      |
        | Open Excel          |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Get Column Count    |  TestSheet1                                        |

        """
        sheet = self.wb.sheet_by_name(sheetname)
        return sheet.ncols

    def get_row_count(self, sheetname):
        """
        Returns the specific number of rows of the sheet name specified.

        Arguments:
                |  Sheet Name (string)  | The selected sheet that the row count will be returned from. |
        Example:

        | *Keywords*          |  *Parameters*                                      |
        | Open Excel          |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Get Row Count       |  TestSheet1                                        |

        """
        sheet = self.wb.sheet_by_name(sheetname)
        return sheet.nrows

    def get_column_values(self, sheetname, column, includeEmptyCells=True):
        """
        Returns the specific column values of the sheet name specified.

        Arguments:
                |  Sheet Name (string)                 | The selected sheet that the column values will be returned from.                                                            |
                |  Column (int)                        | The column integer value that will be used to select the column from which the values will be returned.                     |
                |  Include Empty Cells (default=True)  | The empty cells will be included by default. To deactivate and only return cells with values, pass 'False' in the variable. |
        Example:

        | *Keywords*           |  *Parameters*                                          |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |   |
        | Get Column Values    |  TestSheet1                                        | 0 |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        sheet = self.wb.sheet_by_index(my_sheet_index)
        data = {}
        for row_index in range(sheet.nrows):
            cell = cellname(row_index, int(column))
            value = sheet.cell(row_index, int(column)).value
            data[cell] = value
        if includeEmptyCells is True:
            sortedData = natsort.natsorted(data.items(), key=itemgetter(0))
            return sortedData
        else:
            data = dict([(k, v) for (k, v) in data.items() if v])
            OrderedData = natsort.natsorted(data.items(), key=itemgetter(0))
            return OrderedData

    def get_row_values(self, sheetname, row, includeEmptyCells=True):
        """
        Returns the specific row values of the sheet name specified.

        Arguments:
                |  Sheet Name (string)                 | The selected sheet that the row values will be returned from.                                                               |
                |  Row (int)                           | The row integer value that will be used to select the row from which the values will be returned.                           |
                |  Include Empty Cells (default=True)  | The empty cells will be included by default. To deactivate and only return cells with values, pass 'False' in the variable. |
        Example:

        | *Keywords*           |  *Parameters*                                          |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |   |
        | Get Row Values       |  TestSheet1                                        | 0 |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        sheet = self.wb.sheet_by_index(my_sheet_index)
        data = {}
        for col_index in range(sheet.ncols):
            cell = cellname(int(row), col_index)
            value = sheet.cell(int(row), col_index).value
            data[cell] = value
        if includeEmptyCells is True:
            sortedData = natsort.natsorted(data.items(), key=itemgetter(0))
            return sortedData
        else:
            data = dict([(k, v) for (k, v) in data.items() if v])
            OrderedData = natsort.natsorted(data.items(), key=itemgetter(0))
            return OrderedData

    def get_sheet_values(self, sheetname, includeEmptyCells=True):
        """
        Returns the values from the sheet name specified.

        Arguments:
                |  Sheet Name (string)                 | The selected sheet that the cell values will be returned from.                                                              |
                |  Include Empty Cells (default=True)  | The empty cells will be included by default. To deactivate and only return cells with values, pass 'False' in the variable. |
        Example:

        | *Keywords*           |  *Parameters*                                      |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Get Sheet Values     |  TestSheet1                                        |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        sheet = self.wb.sheet_by_index(my_sheet_index)
        data = {}
        for row_index in range(sheet.nrows):
            for col_index in range(sheet.ncols):
                cell = cellname(row_index, col_index)
                value = sheet.cell(row_index, col_index).value
                data[cell] = value
        if includeEmptyCells is True:
            sortedData = natsort.natsorted(data.items(), key=itemgetter(0))
            return sortedData
        else:
            data = dict([(k, v) for (k, v) in data.items() if v])
            OrderedData = natsort.natsorted(data.items(), key=itemgetter(0))
            return OrderedData

    def get_workbook_values(self, includeEmptyCells=True):
        """
        Returns the values from each sheet of the current workbook.

        Arguments:
                |  Include Empty Cells (default=True)  | The empty cells will be included by default. To deactivate and only return cells with values, pass 'False' in the variable. |
        Example:

        | *Keywords*           |  *Parameters*                                      |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Get Workbook Values  |                                                    |

        """
        sheetData = []
        workbookData = []
        for sheet_name in self.sheetNames:
            if includeEmptyCells is True:
                sheetData = self.get_sheet_values(sheet_name)
            else:
                sheetData = self.get_sheet_values(sheet_name, False)
            sheetData.insert(0, sheet_name)
            workbookData.append(sheetData)
        return workbookData

    def read_cell_data_by_name(self, sheetname, cell_name):
        """
        Uses the cell name to return the data from that cell.

        Arguments:
                |  Sheet Name (string)  | The selected sheet that the cell value will be returned from.  |
                |  Cell Name (string)   | The selected cell name that the value will be returned from.   |
        Example:

        | *Keywords*           |  *Parameters*                                             |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |      |
        | Get Cell Data        |  TestSheet1                                        |  A2  |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        sheet = self.wb.sheet_by_index(my_sheet_index)
        for row_index in range(sheet.nrows):
            for col_index in range(sheet.ncols):
                cell = cellname(row_index, col_index)
                if cell_name == cell:
                    cellValue = sheet.cell(row_index, col_index).value
        return cellValue

    def read_cell_data_by_coordinates(self, sheetname, column, row):
        """
        Uses the column and row to return the data from that cell.

        Arguments:
                |  Sheet Name (string)  | The selected sheet that the cell value will be returned from.         |
                |  Column (int)         | The column integer value that the cell value will be returned from.   |
                |  Row (int)            | The row integer value that the cell value will be returned from.      |
        Example:

        | *Keywords*     |  *Parameters*                                              |
        | Open Excel     |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |   |   |
        | Read Cell      |  TestSheet1                                        | 0 | 0 |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        sheet = self.wb.sheet_by_index(my_sheet_index)
        cellValue = sheet.cell(int(row), int(column)).value
        return cellValue

    def check_cell_type(self, sheetname, column, row):
        """
        Checks the type of value that is within the cell of the sheet name selected.

        Arguments:
                |  Sheet Name (string)  | The selected sheet that the cell type will be checked from.          |
                |  Column (int)         | The column integer value that will be used to check the cell type.   |
                |  Row (int)            | The row integer value that will be used to check the cell type.      |
        Example:

        | *Keywords*           |  *Parameters*                                              |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |   |   |
        | Check Cell Type      |  TestSheet1                                        | 0 | 0 |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        sheet = self.wb.sheet_by_index(my_sheet_index)
        cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
        if cell.ctype is XL_CELL_NUMBER:
            print("The cell value is a number")
        elif cell.ctype is XL_CELL_TEXT:
            print("The cell value is a string")
        elif cell.ctype is XL_CELL_DATE:
            print("The cell value is a date")
        elif cell.ctype is XL_CELL_BOOLEAN:
            print("The cell value is a boolean operator")
        elif cell.ctype is XL_CELL_ERROR:
            print("The cell value has an error")
        elif cell.ctype is XL_CELL_BLANK:
            print("The cell value is blank")
        elif cell.ctype is XL_CELL_EMPTY:
            print("The cell value is empty")
        else:
            print(error_text_from_code[sheet.cell(row, column).value])

    def put_number_to_cell(self, sheetname, column, row, value):
        """
        Using the sheet name the value of the indicated cell is set to be the number given in the parameter.

        Arguments:
                |  Sheet Name (string) | The selected sheet that the cell will be modified from.                                           |
                |  Column (int)        | The column integer value that will be used to modify the cell.                                    |
                |  Row (int)           | The row integer value that will be used to modify the cell.                                       |
                |  Value (int)         | The integer value that will be added to the specified sheetname at the specified column and row.  |
        Example:

        | *Keywords*           |  *Parameters*                                                         |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |     |     |      |
        | Put Number To Cell   |  TestSheet1                                        |  0  |  0  |  34  |

        """
        if self.wb:
            my_sheet_index = self.sheetNames.index(sheetname)
            cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
            if cell.ctype is XL_CELL_NUMBER:
                self.wb.sheets()
                if not self.tb:
                    self.tb = copy(self.wb)
        if self.tb:
            plain = easyxf('')
            self.tb.get_sheet(my_sheet_index).write(int(row), int(column), float(value), plain)

    def put_string_to_cell(self, sheetname, column, row, value):
        """
        Using the sheet name the value of the indicated cell is set to be the string given in the parameter.

        Arguments:
                |  Sheet Name (string) | The selected sheet that the cell will be modified from.                                           |
                |  Column (int)        | The column integer value that will be used to modify the cell.                                    |
                |  Row (int)           | The row integer value that will be used to modify the cell.                                       |
                |  Value (string)      | The string value that will be added to the specified sheetname at the specified column and row.   |
        Example:

        | *Keywords*           |  *Parameters*                                                           |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |     |     |        |
        | Put String To Cell   |  TestSheet1                                        |  0  |  0  |  Hello |

        """
        if self.wb:
            my_sheet_index = self.sheetNames.index(sheetname)
            cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
            if cell.ctype is XL_CELL_TEXT:
                self.wb.sheets()
                if not self.tb:
                    self.tb = copy(self.wb)
        if self.tb:
            plain = easyxf('')
            self.tb.get_sheet(my_sheet_index).write(int(row), int(column), value, plain)

    def put_date_to_cell(self, sheetname, column, row, value):
        """
        Using the sheet name the value of the indicated cell is set to be the date given in the parameter.

        Arguments:
                |  Sheet Name (string)               | The selected sheet that the cell will be modified from.                                                            |
                |  Column (int)                      | The column integer value that will be used to modify the cell.                                                     |
                |  Row (int)                         | The row integer value that will be used to modify the cell.                                                        |
                |  Value (int)                       | The integer value containing a date that will be added to the specified sheetname at the specified column and row. |
        Example:

        | *Keywords*           |  *Parameters*                                                               |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |     |     |            |
        | Put Date To Cell     |  TestSheet1                                        |  0  |  0  |  12.3.1999 |

        """
        if self.wb:
            my_sheet_index = self.sheetNames.index(sheetname)
            cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
            if cell.ctype is XL_CELL_DATE:
                self.wb.sheets()
                if not self.tb:
                    self.tb = copy(self.wb)
        if self.tb:
            print(value)
            dt = value.split('.')
            dti = [int(dt[2]), int(dt[1]), int(dt[0])]
            print(dt, dti)
            ymd = datetime(*dti)
            plain = easyxf('', num_format_str='d.M.yyyy')
            self.tb.get_sheet(my_sheet_index).write(int(row), int(column), ymd, plain)

    def modify_cell_with(self, sheetname, column, row, op, val):
        """
        Using the sheet name a cell is modified with the given operation and value.

        Arguments:
                |  Sheet Name (string)  | The selected sheet that the cell will be modified from.                                                  |
                |  Column (int)         | The column integer value that will be used to modify the cell.                                           |
                |  Row (int)            | The row integer value that will be used to modify the cell.                                              |
                |  Operation (operator) | The operation that will be performed on the value within the cell located by the column and row values.  |
                |  Value (int)          | The integer value that will be used in conjuction with the operation parameter.                          |
        Example:

        | *Keywords*           |  *Parameters*                                                               |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |     |     |     |      |
        | Modify Cell With     |  TestSheet1                                        |  0  |  0  |  *  |  56  |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
        curval = cell.value
        if cell.ctype is XL_CELL_NUMBER:
            self.wb.sheets()
            if not self.tb:
                self.tb = copy(self.wb)
            plain = easyxf('')
            modexpr = str(curval) + op + val
            self.tb.get_sheet(my_sheet_index).write(int(row), int(column), eval(modexpr), plain)

    def add_to_date(self, sheetname, column, row, numdays):
        """
        Using the sheet name the number of days are added to the date in the indicated cell.

        Arguments:
                |  Sheet Name (string)             | The selected sheet that the cell will be modified from.                                                                          |
                |  Column (int)                    | The column integer value that will be used to modify the cell.                                                                   |
                |  Row (int)                       | The row integer value that will be used to modify the cell.                                                                      |
                |  Number of Days (int)            | The integer value containing the number of days that will be added to the specified sheetname at the specified column and row.   |
        Example:

        | *Keywords*           |  *Parameters*                                                        |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |     |     |     |
        | Add To Date          |  TestSheet1                                        |  0  |  0  |  4  |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
        if cell.ctype is XL_CELL_DATE:
            self.wb.sheets()
            if not self.tb:
                self.tb = copy(self.wb)
            curval = datetime(*xldate_as_tuple(cell.value, self.wb.datemode))
            newval = curval + timedelta(int(numdays))
            plain = easyxf('', num_format_str='d.M.yyyy')
            self.tb.get_sheet(my_sheet_index).write(int(row), int(column), newval, plain)

    def subtract_from_date(self, sheetname, column, row, numdays):
        """
        Using the sheet name the number of days are subtracted from the date in the indicated cell.

        Arguments:
                |  Sheet Name (string)             | The selected sheet that the cell will be modified from.                                                                                 |
                |  Column (int)                    | The column integer value that will be used to modify the cell.                                                                          |
                |  Row (int)                       | The row integer value that will be used to modify the cell.                                                                             |
                |  Number of Days (int)            | The integer value containing the number of days that will be subtracted from the specified sheetname at the specified column and row.   |
        Example:

        | *Keywords*           |  *Parameters*                                                        |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |     |     |     |
        | Subtract From Date   |  TestSheet1                                        |  0  |  0  |  7  |

        """
        my_sheet_index = self.sheetNames.index(sheetname)
        cell = self.wb.get_sheet(my_sheet_index).cell(int(row), int(column))
        if cell.ctype is XL_CELL_DATE:
            self.wb.sheets()
            if not self.tb:
                self.tb = copy(self.wb)
            curval = datetime(*xldate_as_tuple(cell.value, self.wb.datemode))
            newval = curval - timedelta(int(numdays))
            plain = easyxf('', num_format_str='d.M.yyyy')
            self.tb.get_sheet(my_sheet_index).write(int(row), int(column), newval, plain)

    def save_excel(self, filename, useTempDir=False):
        """
        Saves the Excel file indicated by file name, the useTempDir can be set to true if the user needs the file saved in the temporary directory.
        If the boolean useTempDir is set to true, depending on the operating system of the computer running the test the file will be saved in the Temp directory if the operating system is Windows or tmp directory if it is not.

        Arguments:
                |  File Name (string)                      | The name of the of the file to be saved.  |
                |  Use Temporary Directory (default=False) | The file will not be saved in a temporary directory by default. To activate and save the file in a temporary directory, pass 'True' in the variable. |
        Example:

        | *Keywords*           |  *Parameters*                                      |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Save Excel           |  NewExcelRobotTest.xls                             |

        """
        if useTempDir is True:
            print('*DEBUG* Got fname %s' % filename)
            self.tb.save(os.path.join("/", self.tmpDir, filename))
        else:
            self.tb.save(filename)

    def save_excel_current_directory(self, filename):
        """
        Saves the Excel file from the current directory using the directory the test has been run from.

        Arguments:
                |  File Name (string)    | The name of the of the file to be saved.  |
        Example:

        | *Keywords*                     |  *Parameters*                                      |
        | Open Excel                     |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Save Excel Current Directory   |  NewTestCases.xls                                  |

        """
        workdir = os.getcwd()
        print('*DEBUG* Got fname %s' % filename)
        self.tb.save(os.path.join(workdir, filename))

    def add_new_sheet(self, newsheetname):
        """
        Creates and appends new Excel worksheet using the new sheet name to the current workbook.

        Arguments:
                |  New Sheet name (string)  | The name of the new sheet added to the workbook.  |
        Example:

        | *Keywords*           |  *Parameters*                                      |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Add New Sheet        |  NewSheet                                          |

        """
        self.tb = copy(self.wb)
        self.tb.add_sheet(newsheetname)

    def create_excel_workbook(self, newsheetname):
        """
        Creates a new Excel workbook

        Arguments:
                |  New Sheet Name (string)  | The name of the new sheet added to the new workbook.  |
        Example:

        | *Keywords*           |  *Parameters*                                      |
        | Open Excel           |  C:\\Python27\\ExcelRobotTest\\ExcelRobotTest.xls  |
        | Create Excel         |  NewExcelSheet                                     |

        """
        self.tb = Workbook()
        self.tb.add_sheet(newsheetname)
