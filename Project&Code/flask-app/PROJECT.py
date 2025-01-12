import os
from pyspark.sql import SparkSession
from pyspark.sql import functions
from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
#import plotly.io as pio
from datetime import datetime, timedelta
import time
from app.utils.Funzioni_Spark import *
import json
import logging 

logging.basicConfig(level=logging.INFO)

time.sleep(1)
app = Flask(__name__, template_folder=os.path.abspath('app/templates'), static_folder=os.path.abspath('app/static'))

master = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
spark_ses = SparkSession.builder \
    .appName("Esecutore") \
    .master(master) \
    .config("spark.cores.max", "8") \
    .config("spark.executor.memory", "4gb") \
    .config("spark.scheduler.mode", "FAIR") \
    .getOrCreate()
spark_ses.sparkContext.setLogLevel("ERROR")

@app.route("/", methods=["GET", "POST"])
def home():        
    #ANALISI IN POST
    date_start=datetime.now().date()-timedelta(days=1)
    date_end=datetime.now().date()
    country=""
    if request.method == "POST":
        try:
            date_start=request.form.get("start_date")
            date_end=request.form.get("end_date")
            country=request.form.get("country")
            cameo_code = json.loads(request.form.get("selectedCodes", "[]"))
            pipeline=build_query(try_int(date_start), try_int(date_end), country, cameo_code)
            print(pipeline, flush=True)
            generale=spark_read_mongo(spark_ses,pipeline)
            if generale is None or generale.count() == 0:
                raise Exception("Non ci sono dati!")
        except Exception as e:
            print(f"Errore nella lettura: {e}", flush=True)
            return render_template("index.html", tipo_evento=None)
    #ANALISI IN GET (USARE BATCH!)
    try:
        if request.method=="GET":
            generale=spark_read_batch(spark_ses, "most_mentioned_view")
        lista_paesi = generale.select("ActionGeo_CountryCode").distinct().rdd.flatMap(lambda x: x).collect()
        general_map=generate_map(generale, "NumMentions", type="generals") #Prendo quelli con NumMentions maggiore
        eventi_menzionati=generate_visualize(generale, "CAMEOCodeDescription", "count").sort_values(ascending=False).head(5)
        tono_medio=round(generale.select(functions.mean("AvgTone")).first()[0],2)
        ist_tono=generate_ist(generale, "AvgTone", tono_medio)
        titolo=crea_titolo(date_start, date_end)
        return render_template("index.html", map_plot=general_map, tipo_evento=eventi_menzionati,
                            titolo=titolo, 
                            lista_paesi=lista_paesi,
                            tono_medio=tono_medio,
                            ist_plot=ist_tono, 
                            date_start=date_start,
                            date_end=date_end, country=country, selezionati=None)
    except Exception as e:
        print(f"Errore nella lettura: {e}", flush=True)
        return render_template("index.html", tipo_evento=None)

@app.route("/GoodVibes", methods=["GET", "POST"])
def good_vibes():
    date_start=datetime.now().date()-timedelta(days=1)
    date_end=datetime.now().date()
    country=""
    #PARTE POST
    if request.method == "POST":
        try:
            date_start=request.form.get("start_date")
            date_end=request.form.get("end_date")
            country=request.form.get("country")
            cameo_code = json.loads(request.form.get("selectedCodes", "[]"))
            pipeline=build_query(try_int(date_start), try_int(date_end), country, cameo_code, type="good")
            good=spark_read_mongo(spark_ses,pipeline)
            if good is None or good.count() == 0:
                raise Exception("Non ci sono dati!")
        except Exception as e:
            print(f"Errore nella lettura: {e}", flush=True)
            return render_template("good_vibes.html", tipo_evento=None)

    #PARTE GET
    try:
        if request.method=="GET":
            good=spark_read_batch(spark_ses, "best_events_view")
        lista_paesi = good.select("ActionGeo_CountryCode").distinct().rdd.flatMap(lambda x: x).collect()
        good_map=generate_map(good, "GoldsteinScale", type="migliori", color="green")
        tutti_gli_eventi=generate_visualize(good, "CAMEOCodeDescription", "count").sort_values(ascending=False)
        tipo_evento=tutti_gli_eventi.head(5)

        titolo=crea_titolo(date_start, date_end)
       
        good_paesi_tutti=generate_visualize(good, "ActionGeo_CountryCode", "count", what_return="ActionGeo_CountryCode")
        good_paesi_five=good_paesi_tutti.sort_values(ascending=False).head(5)
        
        five_best_news=good.sort("AvgTone", "GoldsteinScale", ascending=False).limit(5).toPandas().to_dict(orient="records")
        
        nominati_e_good=good.sort("NumMentions", ascending=False).limit(5).toPandas().to_dict(orient="records")
        
        paesi_tono_medio=generate_visualize(good, ["EventCode","CAMEOCodeDescription"], "avg", what_return=['GoldsteinScale', 'AvgTone'])
        paesi_tono_medio=paesi_tono_medio.reset_index()
        good_pie_tono=generate_pie(paesi_tono_medio, "AvgTone", titolo="Distribuzione Cameo per tono della notizia")
        good_pie_goldstein=generate_pie(paesi_tono_medio, "GoldsteinScale", titolo="Distribuzione Cameo per GoldsteinScale")
        tono_medio=round(good.select(functions.mean("AvgTone")).first()[0],2)
        if len(good_paesi_tutti)>1:
            good_bar=generate_bar(good_paesi_tutti, "Numero di Good News per paese")
        else:
            good_bar=None
        return render_template("good_vibes.html", map_plot=good_map,titolo=titolo, lista_paesi=lista_paesi, tipo_evento=tipo_evento,
                           pie_plot1=good_pie_tono, pie_plot2=good_pie_goldstein, bar_plot=good_bar, best_country=good_paesi_five.to_dict(),
                           best_news=five_best_news, best_menzionate=nominati_e_good,
                           date_start=date_start, date_end=date_end, country=country, tono_medio=tono_medio)
    except Exception as e:
        print("Sono qui", flush=True)
        print(f"Errore nella lettura: {e}", flush=True)
        return render_template("good_vibes.html", tipo_evento=None)
    

@app.route("/BadVibes", methods=["GET", "POST"])
def bad_vibes():
    date_start=datetime.now().date()-timedelta(days=1)
    date_end=datetime.now().date()
    country=""
    #PARTE POST
    if request.method == "POST":
        try:
            date_start=request.form.get("start_date")
            date_end=request.form.get("end_date")
            country=request.form.get("country")
            cameo_code = json.loads(request.form.get("selectedCodes", "[]"))
            pipeline=build_query(try_int(date_start), try_int(date_end), country, cameo_code, type="bad")
            bad=spark_read_mongo(spark_ses,pipeline)
            if bad is None or bad.count() == 0:
                raise Exception("Non ci sono dati!")
        except Exception as e:
            print(f"Errore nella lettura: {e}", flush=True)
            return render_template("bad_vibes.html", tipo_evento=None)

    #PARTE GET
    try:
        if request.method=="GET":
            bad=spark_read_batch(spark_ses, "worst_events_view")
        lista_paesi = bad.select("ActionGeo_CountryCode").distinct().rdd.flatMap(lambda x: x).collect()
        bad_map=generate_map(bad, "GoldsteinScale", type="peggiori", color="red")
        tutti_gli_eventi=generate_visualize(bad, "CAMEOCodeDescription", "count").sort_values(ascending=False)
        tipo_evento=tutti_gli_eventi.head(5)

        titolo=crea_titolo(date_start, date_end)
       
        bad_paesi_tutti=generate_visualize(bad, "ActionGeo_CountryCode", "count", what_return="ActionGeo_CountryCode")
        bad_paesi_five=bad_paesi_tutti.sort_values(ascending=True).tail(5)
        
        five_worst_news=bad.sort("AvgTone", "GoldsteinScale", ascending=True).limit(5).toPandas().to_dict(orient="records")
        
        nominati_e_bad=bad.sort("NumMentions", ascending=False).limit(5).toPandas().to_dict(orient="records")
        
        paesi_tono_medio=generate_visualize(bad, ["EventCode","CAMEOCodeDescription"], "avg", what_return=['GoldsteinScale', 'AvgTone'])
        paesi_tono_medio=paesi_tono_medio.reset_index()
        good_pie_tono=generate_pie(paesi_tono_medio, "AvgTone", titolo="Distribuzione Cameo per tono della notizia")
        good_pie_goldstein=generate_pie(paesi_tono_medio, "GoldsteinScale", titolo="Distribuzione Cameo per GoldsteinScale")
        tono_medio=round(bad.select(functions.mean("AvgTone")).first()[0],2)
        if len(bad_paesi_tutti)>1:
            worst_bar=generate_bar(bad_paesi_tutti, "Numero di Good News per paese")
        else:
            worst_bar=None
        return render_template("bad_vibes.html", map_plot=bad_map,titolo=titolo, lista_paesi=lista_paesi, tipo_evento=tipo_evento,
                           pie_plot1=good_pie_tono, pie_plot2=good_pie_goldstein, bar_plot=worst_bar, worst_country=bad_paesi_five.to_dict(),
                           worst_news=five_worst_news, worst_menzionate=nominati_e_bad,
                           date_start=date_start, date_end=date_end, country=country, tono_medio=tono_medio)
    except Exception as e:
        print("Sono qui", flush=True)
        print(f"Errore nella lettura: {e}", flush=True)
        return render_template("bad_vibes.html", tipo_evento=None)

if __name__ == "__main__":
    time.sleep(1)
    app.run(host="0.0.0.0", port=5000)
    spark_ses.stop()
    