FROM python:3.9

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir output

CMD [ "python3", "ssm-parameter-store-report.py"]
