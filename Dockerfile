FROM python:3.9.14-slim-buster

WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y gcc g++ git python3-opencv
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./requirements.txt /app/requirements.txt
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e git+https://github.com/nxquang-al/detectron2.git#egg=detectron2

EXPOSE 8080
CMD  ["python", "server.py"]