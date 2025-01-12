FROM apache/spark:latest

USER root
COPY connettore.jar /opt/spark/jars/
COPY mongo-java-driver-3.12.10.jar /opt/spark/jars/

RUN apt-get update && \
    apt-get install -y python3-pip && \
    apt-get clean

#RUN apt-get update && \
#    apt-get install -y openjdk-17-jdk-headless python3 python3-pip && \
#    apt-get clean

#ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
#ENV PATH="$JAVA_HOME/bin:${PATH}"

# Installa le dipendenze Python
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# Copia il connettore MongoDB per Spark

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file dell'applicazione Flask nella directory di lavoro
COPY connettore.jar /opt/spark/jars/
COPY mongo-java-driver-3.12.10.jar /opt/spark/jars
COPY . . /app/

EXPOSE 5000

# Imposta il comando di avvio per Flask
CMD ["python3", "PROJECT.py"]
