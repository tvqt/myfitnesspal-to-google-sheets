# myfitnesspal-to-google-sheets
Copy daily MyFitnessPal data to Google Sheets.

Usage: `mfp_sheets.py <MFP username>`

You need to [authorise pygsheets](https://pygsheets.readthedocs.io/en/stable/authorization.html) and [authenticate python-myfitnesspal](https://github.com/coddingtonbear/python-myfitnesspal#authentication).
The script expects a spreadsheet called "Fitness data" in the root folder of your Google Drive, containing a worksheet called "MFP data", with the first column containing dates.
Any columns labelled with the following (ignoring case and anything after the first non-alphanumeric character) will be filled automatically for each day after the last date entered:

* Kilojoules (or Intake)
* Exercise
* Goal
* Protein
* Carbohydrates (or Carbs)
* Fat
* Sugar
* Sodium
* Weight
