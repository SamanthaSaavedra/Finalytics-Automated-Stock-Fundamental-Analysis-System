FROM python:3.13-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping 

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8100
ENTRYPOINT ["bash", "-c", "chmod +x /app/services/start.sh && exec /app/services/start.sh"]