#!/usr/bin/env python3

from datetime import datetime, timedelta
import re
import sys

import pygsheets
import myfitnesspal

FMT = "%Y-%m-%d"


def _date_range(start, end=datetime.today()):
    return [datetime.fromordinal(i) for i in range(start.toordinal(), end.toordinal())]


def _get_col(sheet: pygsheets.Worksheet, index: int):
    """Get column number `index` from the worksheet.

    Returns:
        list[pygsheets.Cell]: A list of references to the cells in the column,
            excluding empty cells at the end.
    """
    return sheet.get_col(index, returnas="cell", include_tailing_empty=False)



def _get_row(sheet: pygsheets.Worksheet, index: int):
    """Get row number `index` from the worksheet.

    Returns:
        list[pygsheets.Cell]: A list of references to the cells in the row, excluding
            empty cells at the end.
    """
    return sheet.get_row(index, returnas="cell", include_tailing_empty=False)


def _get_nutrient_to_col_mapping(header_row):
    """Calculate a mapping of nutrients to column numbers from the header row.

    Returns:
        dict[str, int]: {MFP nutrient name: worksheet column index} mapping.
    """
    mapping = {}
    for cell in header_row:
        nutrient = cell.value.lower()
        if not nutrient.isalpha():
            # Strip units
            try:
                nutrient = re.match(r"\w+", nutrient).group()
            except AttributeError:
                print("Invalid nutrient", nutrient)
        if nutrient == "intake":
            nutrient = "kilojoules"
        mapping[nutrient] = cell.col - 1
    return mapping



def update_sheet_from_mfp(mfp_client, sheet):
    username = mfp_client.user_metadata["username"]

    last_cell = _get_col(sheet, 1)[-1]
    row = last_cell.row
    last_date = datetime.strptime(last_cell.value, FMT)

    # TODO: Detect header
    nutr_to_column = _get_nutrient_to_col_mapping(_get_row(sheet, 2))

    for date in _date_range(last_date + timedelta(days=1)):
        print("Updating", date.date())
        row += 1
        nutrs = [None] * len(nutr_to_column)
        nutrs[0] = date.strftime(FMT)

        # TODO: Add goals, exercise, weight
        mfp_nutrs = mfp_client.get_date(date, username=username)
        for nutrient, amount in mfp_nutrs.totals.items():
            if nutrient in nutr_to_column:
                #print(f"{nutrient}: {amount}")
                nutrs[nutr_to_column[nutrient]] = amount
        sheet.update_values((row, 1), [nutrs])


if __name__ == "__main__":
    print("Connecting to MyFitnessPal...")
    mfp_client = myfitnesspal.Client(sys.argv[1])
    gs_client = pygsheets.authorize()
    print("Opening spreadsheet...")
    # TODO: detect if sheet exists
    sheet = gs_client.open("Fitness data").worksheet("title", "MFP nutrition")
    update_sheet_from_mfp(mfp_client, sheet)
