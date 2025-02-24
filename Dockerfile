FROM python:3.12-alpine

WORKDIR /usr/src/app/

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY ./requirements.txt /usr/src/app/requirements.txt

COPY . /usr/src/app/

RUN pip install -r requirements.txt
CMD [ "python3", "./manage.py", "runserver", "0.0.0.0:8000" ]

# docker build -t threaddit:1.0 .