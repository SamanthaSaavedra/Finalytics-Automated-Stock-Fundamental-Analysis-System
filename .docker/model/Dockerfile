FROM pytorch/pytorch:2.7.0-cuda11.8-cudnn9-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    iputils-ping 

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["bash", "-c", "chmod +x /app/rag/start.sh && exec /app/rag/start.sh"]