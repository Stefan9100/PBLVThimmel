import warnings
from datetime import datetime, timedelta, time

warnings.filterwarnings("ignore", category=DeprecationWarning)
import pandas as pd

# Define the Excel file path
excel_file = 'Input_StudVers.xlsx'
pv_powerHeader = ['Tag', 'Uhrzeit', 'Erzeugung in Watt (W)', 'kummuliert', 'kumuliert in KW']

# Read data from each sheet into a dictionary where keys are sheet names and values are dataframes
pv_powerData = pd.read_excel(excel_file, sheet_name="Erzeugung", usecols=pv_powerHeader)
car_travelData = pd.read_excel(excel_file, sheet_name="Autofahrplan")
car_masterData = {'Modell': ['BMW i4', 'Tesla Model 3'],
                  'Verbrauch in kWh/100km': [14.4, 16.3],
                  'Akkukapazität in kWh': [60, 80],
                  'Ladeleistung in kW': [4, 4],
                  'Anfangsladezustand in %': [10, 10]}

# Put data into pandas DataFrame for use later on
car_masterData = pd.DataFrame(car_masterData)
pv_powerData = pd.DataFrame(pv_powerData)
car_travelData = pd.DataFrame(car_travelData)


# print(pv_powerData.Uhrzeit.to_string())


def decimal_to_time(decimal_hours):
    # Extract integer part (hours) and fractional part (minutes)
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)

    # Create a timedelta object representing the duration
    duration = timedelta(hours=hours, minutes=minutes)
    # print("Dauer: " + str(duration))

    return duration


def subtract_timedelta_from_time(time_obj, timedelta_obj):
    # Convert time object to datetime object with a dummy date
    dummy_date = datetime(1900, 1, 1)
    datetime_obj = datetime.combine(dummy_date, time_obj)

    # Subtract timedelta from datetime object
    result_datetime = datetime_obj - timedelta_obj

    # Extract the time component from the resulting datetime object
    day_difference = abs((result_datetime - dummy_date).days)
    result_time = result_datetime.time()

    return [day_difference, result_time]


def getCurrentChargeState(vehicleNumber):
    startChargePercentage = car_masterData.loc[vehicleNumber - 1, 'Anfangsladezustand in %']
    capacity = car_masterData.loc[vehicleNumber - 1, 'Akkukapazität in kWh']
    currentChargeState = startChargePercentage / 100 * capacity
    return currentChargeState


def getLatestChargePoint(departure_time, departure_day, neededCharge, index):
    # Departure Array mit Tag und Uhrzeit als datetime.time object
    hours_to_neededCharge = neededCharge / 4
    chargeTime = decimal_to_time(hours_to_neededCharge)
    latestChargePoint = subtract_timedelta_from_time(departure_time, chargeTime)
    latestChargePoint_time = latestChargePoint[1]
    latestChargePoint_day = departure_day - latestChargePoint[0]

    return [index, latestChargePoint_day, latestChargePoint_time, chargeTime]


def getLastChargePointsForVehicle(vehicleNumber):
    # endCharge = 10
    drive_schedule = car_travelData[car_travelData['Fahrzeug'] == vehicleNumber]
    # print(drive_schedule.to_string())
    chargePointsArray = []

    # Creates an array that contains that latest start points based on calculation
    for i in drive_schedule.index:
        chargePointsArray.append(getLatestChargePoint(drive_schedule.Abfahrt_Uhrzeit[i], drive_schedule.Abfahrt_Tag[i],
                                                      drive_schedule.Notwendige_Ladung[i], i))
    # print(chargePointsArray)

    # Create data to add to Dataframe

    # print(final_df.to_string())
    # Compares the range between latestCharging to start drive and start drive - end drive to see if the overlap
    """for x in chargePointsArray:
        charge_dummy_date = datetime(99, 12, x[0])
        charge_datetime_obj = datetime.combine(charge_dummy_date, x[1])
        chargeDriveArray_dateObj.append(charge_datetime_obj)
        print(charge_datetime_obj)
    """
    return chargePointsArray


def getChargePointsforAllVehicles():
    # Convert new_data to DataFrame
    array = []
    uniqueFahrzeuge = car_travelData['Fahrzeug'].unique()
    for i in uniqueFahrzeuge:
        array = array + getLastChargePointsForVehicle(i)

    chargePoint_df = pd.DataFrame(array,
                                  columns=['Index', 'Ladezeitpunkt_Tag', 'Ladezeitpunkt_Uhrzeit', 'Dauer']).set_index(
        'Index')
    travel_df = pd.concat([car_travelData, chargePoint_df], axis=1)

    print(travel_df.to_string())


getChargePointsforAllVehicles()
