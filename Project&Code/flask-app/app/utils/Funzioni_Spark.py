from pyspark.sql import SparkSession
from pyspark.sql import functions
import plotly.express as px
import plotly.figure_factory as ff 
import pandas as pd
import numpy as np
from datetime import datetime

from pyspark.sql import SparkSession
import pandas as pd

def spark_read_batch(spark_ses, cosa_leggere="most_mentioned_view"):
    try:
        #le viste sono most_mentioned_view, best_event_view, worst_event_view
        to_return = spark_ses.read \
            .format("mongo") \
            .option("uri", f"mongodb://mongodb:27017/gdelt_batch_views.{cosa_leggere}") \
            .load()
        return to_return
    except Exception as e:
        raise Exception

def spark_read_mongo(spark, pipeline):
    dat=spark.read.format("mongo")\
        .option("uri", "mongodb://mongodb:27017/gdelt_db.gdelt_events")\
        .option("pipeline", pipeline).load()
    if dat.count()==0:
        return None
    dat=dat.select("EventCode","AvgTone","NumMentions","ActionGeo_CountryCode", "ActionGeo_Lat","ActionGeo_Long","CAMEOCodeDescription","SOURCEURL","GoldsteinScale", "SQLDATE", 
            "Actor1Name", "Actor2Name").dropDuplicates()
    return None if dat.count()==0 else dat


def generate_map(dati,on="NumMentions", type="generals", color="blue"):
    if type=="generals":
        treshold=dati.select(functions.mean("NumMentions")+functions.stddev("NumMentions")).first()[0]
        articoli=dati.filter(dati[on]>treshold).toPandas()
    else:
        articoli=dati.toPandas()
    mappa = px.scatter_geo(articoli, lat="ActionGeo_Lat", lon="ActionGeo_Long",
                           hover_name="CAMEOCodeDescription",
                           custom_data=["SOURCEURL", "CAMEOCodeDescription"])
    mappa.update_traces(marker=dict(color=color), hovertemplate="<b>%{hovertext}</b><extra></extra>")
    map_plot = mappa.to_html(mappa, full_html=False)
    return map_plot

def generate_pie(dati, on="AvgTone", titolo=""):
    dati[on]=dati[on].abs()
    fig=px.pie(dati, values=on, names="EventCode", title=titolo, hover_data="CAMEOCodeDescription")
    
    fig.update_traces(textinfo='none', 
                  #showlegend=True
        hovertemplate="<b>%{label}</b><br>%{customdata[0]}<br>Valore: %{value}",)
    pie_plot=fig.to_html(fig, full_html=False)
    return pie_plot

def generate_bar(dati, titolo=""):
    #, y="count"
    fig=px.bar(dati, x="ActionGeo_CountryCode", title=titolo)
    bar_plot=fig.to_html(fig, full_html=False)
    return bar_plot

def generate_ist(dati, on="AvgTone", media=0):
    col="red" if media<0 else "green" if media>0 else "grey"
    ist=px.histogram(dati, x=on, opacity=0.75, color_discrete_sequence=["#636EFA"])
    ist.add_shape(type="line", x0=media, x1=media, y0=0, y1=1, xref="x", yref="paper", line=dict(color=col, width=2, dash="dashdot"), name="Media del periodo")
    ist.update_layout(xaxis_title="Media Tono", yaxis_title="Numero di Articoli")
    ist_plot = ist.to_html(ist, full_html=False)
    return ist_plot

def select_statistics(statistics):
    if statistics=="count":
        return np.size
    elif statistics=="min":
        return np.min
    elif statistics=="max":
        return np.max
    elif statistics=="avg":
        return np.mean
    elif statistics=="stddev":
        return np.std

# type="generals",
def generate_visualize(dat, on="CameoCodeDescription", statistics="count", what_return="SOURCEURL"):
    statistics=select_statistics(statistics)
    return dat.toPandas().groupby(on)[what_return].agg(statistics)

def try_int(dato): 
    try:
        return int(pd.to_datetime(dato).strftime("%Y%m%d"))
    except:
        return None

#QUESTA RESTITUISCE UNA QUERY NO SQL DEL GENERE
#[{"$match": {"SQLDATE": {"$gte": "20240101", "$lte": "20241231"}
# , "ActionGeo_CountryCode": "US", "EventCode": {"$in": ["012", "013", "014"]}}}]
def build_query(start=None, end=None, country=None, event_codes=None, type="general"):
    
    match_conditions = {}
    if start not in (None, "") and end not in (None, ""):
        match_conditions["SQLDATE"] = {"$gte": start, "$lte": end}
    elif start not in (None, ""):
        match_conditions["SQLDATE"] = {"$gte": start}
    elif end not in (None, ""):
        match_conditions["SQLDATE"] = {"$lte": end}
    if country not in (None, ""):
        match_conditions["ActionGeo_CountryCode"] = country
    if event_codes and isinstance(event_codes, list) and len(event_codes) > 0:
        match_conditions["$or"] = [{"EventCode": {"$in": event_codes}},
            {"EventRootCode": {"$in": event_codes}}]
    if type=="good":
        match_conditions["$and"]=[{"GoldsteinScale":{"$gte":5}}, {"AvgTone":{"$gt":0}}]
    elif type=="bad":
        match_conditions["$and"]=[{"GoldsteinScale":{"$lte":-5}}, {"AvgTone":{"$lt":0}}]

    # f'[{{"$match": {match_conditions}}}]'  NON ACCETTATA DA SPARK+MONGO
    pipeline = [{"$match": match_conditions}] #Dovrebbe funzionare così
    return pipeline


def crea_titolo(inizio, fine):
    if inizio is None and fine is None:
        return "Tutti i dati"
    elif inizio is None:
        return f"01/01/2024 A {pd.to_datetime(fine).date()}"
    elif fine is None:
        return f"{pd.to_datetime(str(inizio)).strftime('%Y%m%d')} A {datetime.now().date()}"
    else:
        return f"{pd.to_datetime(str(inizio)).strftime('%Y%m%d')} A {pd.to_datetime(str(fine)).strftime('%Y%m%d')}"
