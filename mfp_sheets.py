#!/usr/bin/env python3

import re
import sys
from datetime import datetime, timedelta

import myfitnesspal
import pygsheets

DATE_FORMAT = "%Y-%m-%d"


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


def _get_header_mapping(sheet):
    """Calculate a mapping of variables to column numbers from the header row.

    Returns:
        dict[str, int]: {MFP nutrient name: worksheet column index} mapping.
        int: Number of cells in row
    """
    for i in range(1, 5):
        try:
            header_row = _get_row(sheet, i)
            if header_row[0].value.lower() == "date":
                break
        except IndexError:
            continue
    else:
        raise ValueError("Could not find header row")

    mapping = {}
    for cell in header_row:
        nutrient = cell.value.lower()
        if not nutrient:
            # Skip padding columns
            continue
        if not nutrient.isalpha():
            # Strip units
            try:
                nutrient = re.match(r"\w+", nutrient).group()
            except AttributeError:
                print("Invalid nutrient", nutrient)
        if nutrient == "intake":
            nutrient = "kilojoules"
        elif nutrient == "carbs":
            nutrient = "carbohydrates"
        mapping[nutrient] = cell.col - 1
    return mapping, len(header_row)


def _get_exercise_for_day(mfp_day: myfitnesspal.day.Day):
    total_burned = 0
    for exercise in mfp_day.exercises:
        for entry in exercise.entries:
            total_burned += entry.nutrition_information["kilojoules burned"]
    return total_burned


def update_sheet_from_mfp(mfp_client: myfitnesspal.Client, sheet: pygsheets.Worksheet):
    last_cell = _get_col(sheet, 1)[-1]
    row = last_cell.row
    last_date = datetime.strptime(last_cell.value, DATE_FORMAT)

    header_mapping, row_length = _get_header_mapping(sheet)
    dates = _date_range(last_date + timedelta(days=1))

    weights = {}
    if "weight" in header_mapping:
        print("Fetching weights...")
        weights = mfp_client.get_measurements(lower_bound=last_date.date())

    for date in dates:
        row += 1
        values = [None] * row_length
        values[0] = date.strftime(DATE_FORMAT)

        print("Updating", date.date())
        mfp_day = mfp_client.get_date(date)  # type: myfitnesspal.day.Day

        # Fill in intake and nutrients,
        for nutrient, amount in mfp_day.totals.items():
            if nutrient in header_mapping:
                # print(f"{nutrient}: {amount}")
                values[header_mapping[nutrient]] = amount

        # Fill in exercise
        if "exercise" in header_mapping:
            values[header_mapping["exercise"]] = _get_exercise_for_day(mfp_day)

        # Fill in goal
        if "goal" in header_mapping:
            values[header_mapping["goal"]] = mfp_day.goals["kilojoules"]

        # Fill in weight
        if "weight" in header_mapping and date.date() in weights:
            values[header_mapping["weight"]] = weights[date.date()]

        sheet.update_row(row, values)


def main():
    print("Connecting to MyFitnessPal...")
    mfp_client = myfitnesspal.Client(sys.argv[1])
    gs_client = pygsheets.authorize()
    print("Opening spreadsheet...")
    # TODO: detect if sheet exists
    sheet = gs_client.open("Fitness data").worksheet("title", "MFP data")
    update_sheet_from_mfp(mfp_client, sheet)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting")
