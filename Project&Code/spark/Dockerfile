FROM apache/spark:latest

USER root

RUN apt-get update && \
    apt-get install -y python3-pip && \
    apt-get clean

RUN pip3 install pyspark
#RUN pip3 install geopy
COPY connettore.jar /opt/spark/jars/
COPY mongo-java-driver-3.12.10.jar /opt/spark/jars
#COPY kafka-clients-3.9.0.jar /opt/spark/jars
#COPY spark-kafka.jar /opt/spark/jars
ENV SPARK_HOME=/opt/spark
#WORKDIR /app
#COPY spark_job_batch.py /app/spark_job_batch.py


USER spark