from kafka import KafkaConsumer
from pymongo import MongoClient
import json

import time

time.sleep(10)

consumer=KafkaConsumer(
    'gdelt_stream',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    fetch_min_bytes=1024,
    fetch_max_wait_ms=500,
    max_poll_records=100) #o 100

client = MongoClient("mongodb://mongodb:27017/")
db=client['gdelt_db']
collection = db["gdelt_events"]

def gia_mandato(id):
    return collection.find_one({'GLOBALEVENTID':id}) is not None

#def count_na(evento):
#    return sum(1 for i in evento.values() if i is not None)

#def controllo_caricamenti(batch):
#    to_return=[]
#    for riga in batch.values():
#        for msg in riga:
#            evento=msg.value
#            if not gia_mandato(evento.get('GLOBALEVENTID')):
#                to_return.append(evento)
#    return to_return

def insert_event(evento):
    if not gia_mandato(evento.get('GLOBALEVENTID')):
        collection.insert_one(evento)
        print("Ho caricato un record in Mongo", flush=True)

def caricamento_batch(batch):
    for riga in batch.values():
        for msg in riga:
            evento=msg.value
            insert_event(evento)
    print("Ho terminato il caricamento del batch dei dati...")

def carica_mongo():
    try:
        while True:
            batch=consumer.poll(timeout_ms=500)
            caricamento_batch(batch)
    except:
        print("Errore durante il caricamento dei dati nel MongoDB")
        print("Riprovo...")
        time.sleep(10)
        carica_mongo()
        #if len(to_insert)>0:
        #    collection.insert_many(to_insert)
        #    print("Ho caricato {} record in Mongo".format(len(to_insert)))
        #else:
        #    print("Nessun dato da caricare in Mongo")
        #time.sleep(120)

if __name__=="__main__":
    carica_mongo()