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
car_travelData['Spaetester-Lade-Tag'] = ''
car_travelData['Spaeteste-Lade-Uhrzeit'] = ''
car_masterData = {'Id': [1, 2],
                  'Modell': ['BMW i4', 'Tesla Model 3'],
                  'Verbrauch in kWh/100km': [60, 80],
                  'Akkukapazität in kWh': [14.4, 16.3],
                  'Ladeleistung in kW': [4, 4],
                  'Anfangsladezustand in %': [10, 10],
                  'IsThere': [False, False]}

# Put data into pandas DataFrame for use later on
car_masterData = pd.DataFrame(car_masterData)
pv_powerData = pd.DataFrame(pv_powerData)
car_travelData = pd.DataFrame(car_travelData)


car_travelData.sort_values(by=["Ankunft-Tag", "Ankunft-Uhrzeit"], inplace=True)
# print Data test
#print(pv_powerData.to_string())
print(car_travelData.to_string())

for index, powerDataEntry in pv_powerData.iterrows():
    if powerDataEntry["Erzeugung in Watt (W)"] > 0:
        for index, travelDataEntry in car_travelData.iterrows():
            arrival_time = travelDataEntry["Ankunft-Uhrzeit"]
            departure_time = travelDataEntry["Abfahrt-Uhrzeit"]
            current_time = powerDataEntry["Uhrzeit"]
            if (travelDataEntry["Ankunft-Tag"] <= powerDataEntry["Tag"]
                and arrival_time <= current_time
                and travelDataEntry["Abfahrt-Tag"] >= powerDataEntry["Tag"]
                and departure_time >= current_time):
                carId = travelDataEntry["Fahrzeug"]
                car_masterData.at[carId, "IsThere"] = True
            else:
                carId = travelDataEntry["Fahrzeug"]
                car_masterData.at[carId, "IsThere"] = False
        print(car_masterData[["Modell", "IsThere"]])
