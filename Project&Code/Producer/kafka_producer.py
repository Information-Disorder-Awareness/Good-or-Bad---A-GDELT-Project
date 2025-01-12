from kafka import KafkaProducer
from gdelt import gdelt
import json
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd
from geopy.geocoders import Nominatim

geolocalizzatore = Nominatim(user_agent="geo_imputer")

time.sleep(10)

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'))


gd2 = gdelt(version=2)
def get_country_code_from_coordinates(lat, lon):
    try:
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            print(f"Latitudine o longitudine non valide: lat={lat}, lon={lon}")
            return None
        location = geolocalizzatore.reverse((lat, lon))
        if location and 'country_code' in location.raw['address']:
            return location.raw['address']['country_code'].upper()
    except Exception as e:
        print(f"Errore nel recupero del codice del paese: {e}")
    return None



def send_data_to_kafka(start_date,  cov=False): #end_date
    try:
        results=gd2.Search(start_date.strftime('%Y %b %d'), coverage=cov, table="events")
        #if last_15:
            #https://pypi.org/project/gdelt/
        #    results=gd2.Search(start_date.strftime('%Y %b %d'), coverage=True, table="events")
        #else:
        #    results = gd2.Search([start_date.strftime('%Y %b %d'), end_date.strftime('%Y %b %d')], coverage=True,table="events")
    except Exception as e:
        print(e)
        return None
        
    for _, row in results.iterrows():
        event_id = row['GLOBALEVENTID']
        action_geo_country_code = row['ActionGeo_CountryCode']
        #Gestione NA
        if pd.isna(action_geo_country_code):  
            action_geo_country_code = get_country_code_from_coordinates(row['ActionGeo_Lat'], row['ActionGeo_Long'])

        actor2_name = row['Actor2Name']
        if pd.isna(actor2_name): 
            actor2_name = action_geo_country_code

        actor1_name = row['Actor1Name']
        if pd.isna(actor1_name):
            actor1_name = actor2_name
        data = {
            "GLOBALEVENTID": event_id,
            "SQLDATE": row['SQLDATE'],
            "MonthYear": row['MonthYear'],
            "Year": row['Year'],
            "Actor1Code": row['Actor1Code'],
            "Actor1Name": actor1_name, #row['Actor1Name'],
            "Actor1CountryCode": row['Actor1CountryCode'],
            "Actor1KnownGroupCode": row["Actor1KnownGroupCode"],
            "Actor2Name": actor2_name,# row['Actor2Name'],
            "Actor2CountryCode": row['Actor2CountryCode'],
            "Actor2KnownGroupCode": row["Actor2KnownGroupCode"],
            "EventCode": row['EventCode'],
            "EventBaseCode": row["EventBaseCode"],
            "EventRootCode": row["EventRootCode"],
            "CAMEOCodeDescription": row['CAMEOCodeDescription'],
            "QuadClass": row["QuadClass"],
            "GoldsteinScale": row['GoldsteinScale'],
            "NumMentions": row['NumMentions'],
            "NumSources": row['NumSources'],
            "NumArticles": row['NumArticles'],
            "AvgTone": row['AvgTone'],
            "ActionGeo_CountryCode":action_geo_country_code, #row['ActionGeo_CountryCode'],
            "ActionGeo_Lat": row['ActionGeo_Lat'],
            "ActionGeo_Long": row['ActionGeo_Long'],
            "DATEADDED": row['DATEADDED'],
            "SOURCEURL": row['SOURCEURL']
        }

        producer.send('gdelt_stream', value=data)
        print(f"Dato inviato a Kafka: {event_id} del {row['SQLDATE']} caricato il {row['DATEADDED']}", flush=True)

def ultimo_evento_salvato():
    client = MongoClient("mongodb://mongodb:27017/")
    db = client["gdelt_db"]
    collection = db["gdelt_events"]
    last_event=collection.find_one({}, sort=[("SQLDATE",-1)], projection={"SQLDATE":1,"_id":0})
    if last_event:
        return datetime.strptime(str(last_event["SQLDATE"]), "%Y%m%d")
    return None

def db_vuoto():
    client = MongoClient("mongodb://mongodb:27017/")
    db = client["gdelt_db"]
    collection = db["gdelt_events"]
    return collection.count_documents({})==0

def prima_popolazione():
    
    if db_vuoto():
        current_date=datetime(2024,1,1)
        end_date=datetime.now()
        #send_data_to_kafka(datetime(2024,1,1), datetime.now())
        #time.sleep(900)        
    else:
        ultima_data=ultimo_evento_salvato()
        if ultima_data:
            current_date=ultima_data
            end_date=datetime.now()
        else:
            current_date=datetime.now()-timedelta(minutes=15)
            end_date=datetime.now()
    while current_date<end_date:
        inizio=datetime.now()
        print(f"INviando dati del {current_date}")
        send_data_to_kafka(current_date, cov=False)
        current_date+=timedelta(days=1)
        fine=datetime.now()
        print(f"Un giorno coverage=True ci ha messo {fine-inizio}")
    print("Popolazione completata")
    #print(f"Inviando dati da {start_date} a {datetime.now()}")
    #send_data_to_kafka(start_date, datetime.now())
    
    
if __name__ == "__main__":
    prima_popolazione()
    time.sleep(600) 
    while True:
        start_date = datetime.now() - timedelta(minutes=15)  
        
        print(f"Eseguendo aggiornamento incrementale da {start_date} a {datetime.now()}")
        response=send_data_to_kafka(start_date,  False) #None
        print(response)
        if response is None:
            time.sleep(300)
        else:
            time.sleep(600)

#https://github.com/alex9smith/gdelt-doc-api
#http://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf