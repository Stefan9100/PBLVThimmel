import warnings
import datetime


warnings.filterwarnings("ignore", category=DeprecationWarning)
import pandas as pd

# Define the Excel file path
excel_file = 'Input_StudVers.xlsx'
pv_powerHeader = ['Tag', 'Uhrzeit', 'Erzeugung in Watt (W)', 'kummuliert', 'kumuliert in KW']

# Read data from each sheet into a dictionary where keys are sheet names and values are dataframes
pv_powerData = pd.read_excel(excel_file, sheet_name="Erzeugung", usecols=pv_powerHeader)
car_travelData = pd.read_excel(excel_file, sheet_name="Autofahrplan")
car_masterData = {'Modell': ['BMW i4', 'Tesla Model 3'],
                  'Verbrauch in kWh/100km': [60, 80],
                  'Akkukapazität in kWh': [14.4, 16.3],
                  'Ladeleistung in kW': [4, 4],
                  'Anfangsladezustand in %': [10, 10]}

# Put data into pandas DataFrame for use later on
car_masterData = pd.DataFrame(car_masterData)
pv_powerData = pd.DataFrame(pv_powerData)
car_travelData = pd.DataFrame(car_travelData)
