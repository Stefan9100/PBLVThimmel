import warnings
from datetime import datetime, timedelta


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
car_travelData.loc[car_travelData['Fahrzeug'] == 1, 'Spaeteste-Lade-Uhrzeit'] = '23:00'  
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

# angenommen spätester Ladezeitpunkt gegeben
# verschiebt die spätere Lade Uhrzeit, wenn davor bereits geladen wurde

def adjust_charging_schedule_based_on_remaining_load(car_travelData, car_id, loaded_kwh):
    # Wie viele kWh in 5 Minuten geladen werden können
    kwh_per_interval = (4 / 60) * 5  
    
    # spezifisches Auto
    car_data = car_travelData[car_travelData['Fahrzeug'] == car_id]
    
    for index, row in car_data.iterrows():
        # verbleibende erforderliche Ladung
        remaining_kwh = row['Notwendige Ladung'] - loaded_kwh
        
        # Sicherstellen, dass verbleibende Ladung nicht negativ
        remaining_kwh = max(remaining_kwh, 0)
        
        # benötigte Intervalle, für verbleibende benötigte Ladung
        intervals_needed = remaining_kwh / kwh_per_interval
        
        # neue späteste Ladezeit basierend auf verbleibende Ladung
        latest_charging_time_str = f"{row['Spaetester-Lade-Tag']} {row['Spaeteste-Lade-Uhrzeit']}"
        latest_charging_time = datetime.strptime(latest_charging_time_str, '%d %H:%M')
        new_latest_charging_time = latest_charging_time + timedelta(minutes=intervals_needed * 5)
        
        # Update den DataFrame mit der neuen spätesten Ladezeit
        car_travelData.at[index, 'Spaeteste-Lade-Uhrzeit'] = new_latest_charging_time.strftime('%H:%M')
    
    return car_travelData

# Test
adjusted_car_travelData = adjust_charging_schedule_based_on_remaining_load(car_travelData, 1, 10)
print(adjusted_car_travelData[['Fahrzeug', 'Ankunft-Tag', 'Ankunft-Uhrzeit', 'Spaetester-Lade-Tag', 'Spaeteste-Lade-Uhrzeit']])


# alte Version Abzug der geladenen kW im 5 Minuten-Takt korrekt jedoch, kein Verschieben der späteren Lade Uhrzeit, da dafür eine Start Ladezeit gegeben sein muss

# def adjust_charging_schedule(car_travelData, car_id, additional_kwh):
  
#     # Wie viele kWh in 5 Minuten geladen werden können
#     kwh_per_interval = (4/ 60) * 5
    
#     # spezifisches Auto
#     car_data = car_travelData[car_travelData['Fahrzeug'] == car_id]

#     for index, row in car_data.iterrows():
#         # benötigte Intervalle, um  zusätzlichen kWs zu laden
#         intervals_needed = additional_kwh / kwh_per_interval
        
#         # neue späteste Ladezeit
#         latest_charging_time_str = f"{row['Spaetester-Lade-Tag']} {row['Spaeteste-Lade-Uhrzeit']}"
#         latest_charging_time = datetime.strptime(latest_charging_time_str, '%d %H:%M')
#         new_latest_charging_time = latest_charging_time + timedelta(minutes=intervals_needed * 5)
        
#         # Update DataFrame mit neuen spätesten Ladezeit
#         car_travelData.at[index, 'Spaeteste-Lade-Uhrzeit'] = new_latest_charging_time.strftime('%H:%M')
        
#         # DataFrame, für Ladevorgang im 5-Minuten-Takt 
#         charging_intervals = pd.DataFrame({
#             'Zeit': [latest_charging_time + timedelta(minutes=5*i) for i in range(int(intervals_needed))],
#             'Geladene kWh': [kwh_per_interval * (i+1) for i in range(int(intervals_needed))]
#         })
        
#         print(f"Ladevorgang für Fahrzeug {car_id} im 5-Minuten-Takt:")
#         print(charging_intervals.to_string(index=False))

#     return car_travelData
