import warnings
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt
from math import isclose

from matplotlib.dates import HourLocator, DateFormatter, MinuteLocator

warnings.filterwarnings("ignore")
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
doc_charge = []


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


def get_active_travel_data_indices(powerDataEntry, car_travelData):
    indices = []
    for index, travelDataEntry in car_travelData.iterrows():
        arrival_time = travelDataEntry["Ankunft"].time()
        departure_time = travelDataEntry["Abfahrt"].time()
        current_time = powerDataEntry["Uhrzeit"]

        if (travelDataEntry["Ankunft"].day > powerDataEntry["Tag"] or
                (travelDataEntry["Ankunft"].day == powerDataEntry["Tag"] and arrival_time > current_time)):
            break
        if ((travelDataEntry["Abfahrt"].day > powerDataEntry["Tag"]
             or (travelDataEntry["Abfahrt"].day == powerDataEntry["Tag"] and departure_time >= current_time))
                and (travelDataEntry["Ankunft"].day < powerDataEntry["Tag"]
                     or (travelDataEntry["Ankunft"].day == powerDataEntry["Tag"] and arrival_time < current_time))):
            indices.append(index)
    return indices


def getNextIndex(current_index, current_car):
    current_car_df = car_travelData[car_travelData['Fahrzeug'] == current_car]
    if current_index +1 > current_car_df.iloc[-1].name:
        return -1
    else:
        next_car = current_car_df.at[current_index + 1, 'Fahrzeug']
        if (current_car == next_car):
            return current_index + 1
        else:
            getNextIndex(current_index + 1, current_car)


def charge(car_travel_index, energy_loaded_in_5_min_kW):
    current_duration = car_travelData.at[car_travel_index, 'Dauer']

    if current_duration > timedelta(0):
        car_travelData.at[car_travel_index, 'Dauer'] = current_duration - timedelta(minutes=5)
        new_chargeNeeded = car_travelData.at[car_travel_index, 'Notwendige_Ladung'] - energy_loaded_in_5_min_kW
        if new_chargeNeeded < 0.5:
            car_travelData.at[car_travel_index, 'Notwendige_Ladung'] = 0
        else:
            car_travelData.at[car_travel_index, 'Notwendige_Ladung'] = new_chargeNeeded
    else:
        next_Index = getNextIndex(car_travel_index, car_travelData.at[car_travel_index, 'Fahrzeug'])
        if next_Index != -1:
            charge(next_Index, energy_loaded_in_5_min_kW)



# -------------------DATEN----------------------------------
# Apply the function to each row
car_travelData['Ankunft'] = car_travelData.apply(
    lambda row: combine_day_and_time(row['Ankunft_Tag'], row['Ankunft_Uhrzeit']), axis=1)
car_travelData['Abfahrt'] = car_travelData.apply(
    lambda row: combine_day_and_time(row['Abfahrt_Tag'], row['Abfahrt_Uhrzeit']), axis=1)
car_travelData['Dauer'] = car_travelData.apply(
    lambda row: getDuration(row['Notwendige_Ladung']), axis=1)
car_travelData = car_travelData.drop(columns=['Ankunft_Tag', 'Ankunft_Uhrzeit', 'Abfahrt_Tag', 'Abfahrt_Uhrzeit'])
car_travelData = adjust_duration(car_travelData)
car_travelData.sort_values(by=["Ankunft"], inplace=True)


# -------------------LOGIK------------------------
def calcPuffer(abfahrt, dauer, powerDataDate):
    puffer = (abfahrt - dauer) - powerDataDate
    return puffer


for index, powerDataEntry in pv_powerData.iterrows():
    active_travel_data_indices = get_active_travel_data_indices(powerDataEntry, car_travelData)
    powerDataDate = combine_day_and_time(powerDataEntry['Tag'], powerDataEntry['Uhrzeit'])
    energy_pv_W = 1000 / 3
    energy_pv_kW = energy_pv_W / 1000
    # Nötig um den Puffer zu berechnen
    active_travel_data = car_travelData.loc[active_travel_data_indices]
    active_travel_data['Puffer'] = car_travelData.apply(
        lambda row: calcPuffer(row['Abfahrt'], row['Dauer'], powerDataDate), axis=1)

    # print("Tag " + str(powerDataDate))

    # Prüfung, ob überhaupt ein Auto da ist
    if len(active_travel_data_indices) == 0:
        continue
    # print(active_travel_data.to_string())

    # Wenn die PV Erzeugung über 4kwh ist
    if powerDataEntry["Erzeugung in Watt (W)"] > 1000 / 3:
        # Wenn nur ein Auto zuhause ist wird dieses geladen
        if len(active_travel_data_indices) == 1:
            # => Load Car von Jasmin active_travel_data_indices[0], 4000/60 * 5, adjusted_car_travelData
            # print(active_travel_data['Dauer'][4])
            doc_charge.append(
                [powerDataDate, active_travel_data.at[active_travel_data_indices[0], 'Fahrzeug'], energy_pv_kW, "PV"])
            charge(active_travel_data_indices[0], energy_pv_kW)
            # print(active_travel_data.to_string())
            # print("Load Car: " + str(active_travel_data_indices[0]) + "; Tag: " + str(powerDataEntry["Tag"])+ "; Uhrzeit: " + str(powerDataEntry["Uhrzeit"]))
            continue
        # Wenn mehere Autos zu hause sind
        else:
            to_much_power = powerDataEntry["Erzeugung in Watt (W)"] - energy_pv_W
            # print("Prio-Check")
            # Können beide Autos gleichzeitig mit PB strom geladen werden
            if to_much_power > energy_pv_W:
                # => Load beide Autos mit PV Strom
                # print("Ohne Prio - Beide werden voll geladen")
                for i in active_travel_data_indices:
                    # PV
                    doc_charge.append([powerDataDate, active_travel_data.at[i, 'Fahrzeug'], energy_pv_kW, "PV"])
                    charge(i, energy_pv_kW)
                # print(active_travel_data.to_string())
                continue
            # Es kann nur ein Auto mit 4kwh Strom geladen werden
            else:
                # print("Mit-Prio Entscheidung:")
                # If puffer bei allen  von beiden 0
                if active_travel_data.at[active_travel_data_indices[0], 'Puffer'] < active_travel_data.at[
                    active_travel_data_indices[1], 'Puffer']:
                    # PV
                    doc_charge.append(
                        [powerDataDate, active_travel_data.at[active_travel_data_indices[0], 'Fahrzeug'], energy_pv_kW,
                         "PV"])
                    charge(active_travel_data_indices[0], energy_pv_kW)
                    if active_travel_data.at[active_travel_data_indices[1], 'Puffer'] <= timedelta(minutes=4,
                                                                                                   seconds=59) and \
                            active_travel_data.at[active_travel_data_indices[1], 'Dauer'] >= timedelta(0):
                        # Netz
                        doc_charge.append(
                            [powerDataDate, active_travel_data.at[active_travel_data_indices[1], 'Fahrzeug'],
                             energy_pv_kW, "Netz"])
                        charge(active_travel_data_indices[1], energy_pv_kW)

                else:
                    # PV
                    doc_charge.append(
                        [powerDataDate, active_travel_data.at[active_travel_data_indices[1], 'Fahrzeug'], energy_pv_kW,
                         "PV"])
                    charge(active_travel_data_indices[1], energy_pv_kW)
                    if active_travel_data.at[active_travel_data_indices[0], 'Puffer'] <= timedelta(minutes=4,
                                                                                                   seconds=59) and \
                            active_travel_data.at[active_travel_data_indices[0], 'Dauer'] >= timedelta(0):
                        # Netz
                        doc_charge.append(
                            [powerDataDate, active_travel_data.at[active_travel_data_indices[0], 'Fahrzeug'],
                             energy_pv_kW, "Netz"])
                        charge(active_travel_data_indices[0], energy_pv_kW)
                # Lade das wo der Puffer weniger ist mit 4kwh
                # Lade das andere mit to_much_power
        # print(active_travel_data.to_string())
    # PV-Strom ist in kleiner Menge verfügbar
    else:
        # if puffer bei beiden 0
        # print("Keine PV")
        if len(active_travel_data_indices) == 0:
            continue
        elif len(active_travel_data_indices) == 1:
            if active_travel_data.at[active_travel_data_indices[0], 'Puffer'] <= timedelta(minutes=4, seconds=59) and \
                    active_travel_data.at[active_travel_data_indices[0], 'Dauer'] >= timedelta(0):
                # Netz
                doc_charge.append(
                    [powerDataDate, active_travel_data.at[active_travel_data_indices[0], 'Fahrzeug'], energy_pv_kW,
                     "Netz"])
                charge(active_travel_data_indices[0], energy_pv_kW)
                continue
        else:
            if active_travel_data.at[active_travel_data_indices[0], 'Puffer'] <= timedelta(minutes=4, seconds=59) and \
                    active_travel_data.at[active_travel_data_indices[0], 'Dauer'] >= timedelta(0):
                # Netz
                doc_charge.append(
                    [powerDataDate, active_travel_data.at[active_travel_data_indices[0], 'Fahrzeug'], energy_pv_kW,
                     "Netz"])
                charge(active_travel_data_indices[0], energy_pv_kW)

            if active_travel_data.at[active_travel_data_indices[1], 'Puffer'] <= timedelta(minutes=4, seconds=59) and \
                    active_travel_data.at[active_travel_data_indices[1], 'Dauer'] >= timedelta(0):
                # Netz
                doc_charge.append(
                    [powerDataDate, active_travel_data.at[active_travel_data_indices[1], 'Fahrzeug'], energy_pv_kW,
                     "Netz"])
                charge(active_travel_data_indices[1], energy_pv_kW)

    # Gibt es Autos wo puffer gleich 0
    # elif ...
    # elif any(active_travel_data_entry == timedelta(0) for active_travel_data_entry in active_travel_data['Puffer']):
    #    print(4)
    # Lade alle Autps wo Puffer gleich 0 mit 4kwh normalen Strom
df = pd.DataFrame(doc_charge)
sorted_df = df.sort_values(by=[1, 0])
print(sorted_df.to_string())
fahrzeug1_df = df[df[1] == 1]
fahrzeug1_Netz_df = fahrzeug1_df[fahrzeug1_df[3] == "Netz"]
fahrzeug1_PV_df = fahrzeug1_df[fahrzeug1_df[3] == "PV"]

fahrzeug2_df = df[df[1] == 2]
fahrzeug2_Netz_df = fahrzeug2_df[fahrzeug2_df[3] == "Netz"]
fahrzeug2_PV_df = fahrzeug2_df[fahrzeug2_df[3] == "PV"]

# Plotting the DataFrame
plt.figure(figsize=(80, 6))
plt.plot_date(fahrzeug1_PV_df[0], fahrzeug1_PV_df[2] * 3, label='PV Strom Fahrzeug 1')
plt.plot_date(fahrzeug1_Netz_df[0], fahrzeug1_Netz_df[2] * 3, label='Netz Strom Fahrzeug 1')
plt.plot_date(fahrzeug2_PV_df[0], fahrzeug2_PV_df[2] * 6, label='PV Strom Fahrzeug 2')
plt.plot_date(fahrzeug2_Netz_df[0], fahrzeug2_Netz_df[2] * 6, label='Netz Strom Fahrzeug 2')

plt.xlabel('Time')

plt.gca().xaxis.set_major_locator(MinuteLocator(interval=30)) # Set interval of 2 hours
plt.gca().xaxis.set_major_formatter(DateFormatter('%d %H:%M'))  # Format datetime as desired

plt.ylabel('Fahrzeug')
plt.title('Ladesignale')
plt.ylim(0, 4)
plt.xticks(rotation=65, fontsize=6)  # Rotate x-axis labels for better visibility
plt.tight_layout()
plt.legend()
# Save the plot as a PNG file with higher DPI

plt.savefig('plot.png', dpi=600)
plt.grid(True)
plt.show()

# print(merge_df.to_string())
