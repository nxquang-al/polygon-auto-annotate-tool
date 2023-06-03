FROM python:3.9.14-slim-buster

WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y gcc g++ git python3-opencv
ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY ./requirements.txt /app/requirements.txt
COPY . /app

# Install packages and dependecies
RUN pip install --no-cache-dir -r requirements.txt
# Build Detectron2 from source, this library has been forked and modified to fit this app,
# please refer the repo in my personal GitHub account for more details.
RUN pip install -e git+https://github.com/nxquang-al/detectron2.git#egg=detectron2
# Download model checkpoint to ./models/
RUN gdown https://drive.google.com/uc?id=1qhoiYU92BvJuum74rY6LpiG7-FoEqoO9 -O ./models/

EXPOSE 8080
# CMD  ["python", "server.py"]
CMD ["gunicorn", "-b", "0.0.0.0:8080", "server:app"]