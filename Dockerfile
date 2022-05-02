FROM python:3.9.6

RUN mkdir /src
WORKDIR /src
COPY . /src
RUN pip install -r requirements.txt