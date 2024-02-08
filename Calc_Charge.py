import warnings
from datetime import datetime, timedelta, time

warnings.filterwarnings("ignore", category=DeprecationWarning)
import pandas as pd

# Define the Excel file path
excel_file = 'Input_StudVers.xlsx'
pv_powerHeader = ['Tag', 'Uhrzeit', 'Erzeugung in Watt (W)', 'kummuliert', 'kumuliert in KW']

pv_powerData = pd.read_excel(excel_file, sheet_name="Erzeugung", usecols=pv_powerHeader)
car_travelData = pd.read_excel(excel_file, sheet_name="Autofahrplan")
car_masterData = {'Id': [1, 2],
                  'Modell': ['BMW i4', 'Tesla Model 3'],
                  'Verbrauch in kWh/100km': [14.4, 16.3],
                  'Akkukapazität in kWh': [60, 80],
                  'Ladeleistung in kW': [4, 4],
                  'Anfangsladezustand in %': [10, 10]}

# Put data into pandas DataFrame for use later on
car_masterData = pd.DataFrame(car_masterData)
car_travelData = pd.DataFrame(car_travelData)
pv_powerData = pd.DataFrame(pv_powerData)


def decimal_to_time(decimal_hours):
    # Extract integer part (hours) and fractional part (minutes)
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)

    # Create a timedelta object representing the duration
    duration = timedelta(hours=hours, minutes=minutes)
    # print("Dauer: " + str(duration))

    return duration


def getDuration(neededCharge):
    # Departure Array mit Tag und Uhrzeit als datetime.time object
    hours_to_neededCharge = neededCharge / 4
    chargeTime = decimal_to_time(hours_to_neededCharge)

    return chargeTime


def combine_day_and_time(day: int, time_obj: time) -> datetime:
    # Dummy values for year and month
    dummy_year = 99
    dummy_month = 12

    # Combine day, time, year, and month to create a datetime object
    return datetime(dummy_year, dummy_month, day, time_obj.hour, time_obj.minute, time_obj.second)


def adjust_duration(travel_dataframe):
    for index, row in travel_dataframe.iterrows():
        abfahrt = row['Abfahrt']
        dauer = row['Dauer']
        if index > 0 and travel_dataframe.at[index - 1, 'Fahrzeug'] == travel_dataframe.at[index, 'Fahrzeug']:
            previous_dauer = travel_dataframe.at[index - 1, 'Dauer']
            ankunft = row['Ankunft']
            if abfahrt - dauer < ankunft:
                travel_dataframe.at[index - 1, 'Dauer'] = previous_dauer + (ankunft - (abfahrt - dauer))
                travel_dataframe.at[index, 'Dauer'] = abfahrt - ankunft
                adjust_duration(travel_dataframe)
    return travel_dataframe


# Apply the function to each row
car_travelData['Ankunft'] = car_travelData.apply(
    lambda row: combine_day_and_time(row['Ankunft_Tag'], row['Ankunft_Uhrzeit']), axis=1)
car_travelData['Abfahrt'] = car_travelData.apply(
    lambda row: combine_day_and_time(row['Abfahrt_Tag'], row['Abfahrt_Uhrzeit']), axis=1)
car_travelData['Dauer'] = car_travelData.apply(
    lambda row: getDuration(row['Notwendige_Ladung']), axis=1)
car_travelData = car_travelData.drop(columns=['Ankunft_Tag', 'Ankunft_Uhrzeit', 'Abfahrt_Tag', 'Abfahrt_Uhrzeit'])
car_travelData = adjust_duration(car_travelData)

print(car_travelData.to_string())
