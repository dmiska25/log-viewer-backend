import json
import random
from faker import Faker
from faker.providers import date_time
import requests 
fake = Faker()
fake.add_provider(date_time)

 # dictionaries
service_names = [
    "Pod1",
    "Pod2",
    "Pod3"
]

severity = [
    'L',
    'M',
    'H',
    'C'
]

type = [
    'I',
    'E',
    'W',
    'S',
    'R'
]



# define classes

class BaseLog:
    def __init__(self, service_name, timestamp, severity, type, title, description) -> None:
        self.service_name = service_name
        self.timestamp = timestamp
        self.severity = severity
        self.type = type
        self.title = title
        self.description = description

    def __str__(self) -> str:
        string = ""
        for attr, value in self.__dict__.items():
            string += f"{attr}={value},"
        return string.strip(',')

    def getDefaultArgs():
        return {
            'service_name': random.choice(service_names), 
            'timestamp': fake.past_datetime().isoformat(sep='T', timespec='auto'), 
            'severity': random.choice(severity), 
            'type': random.choice(type), 
            'title': fake.text(50), 
            'description': fake.text(),
        }

    def generate():
        return BaseLog(**BaseLog.getDefaultArgs())

class ErrorLog(BaseLog):
    def __init__(self, traceback, **kwargs) -> None:
        super().__init__(**kwargs)
        self.traceback = traceback

    def getDefaultArgs():
        return {
            'traceback': "Example",
            **BaseLog.getDefaultArgs()
        }

    def generate():
        return ErrorLog(**ErrorLog.getDefaultArgs())
        


# define generation and quantities
generation = {
    BaseLog: 20,
    #ErrorLog: 10
}


# run generation and serialize
logs = []

for logType in generation:
    for _ in range(generation[logType]):
        logs.append(logType.generate().__dict__)


# send requests
URL = "http://127.0.0.1:8000/api/logs/"

session = requests.Session()
session.auth = ("dmiska", "Whiskers04")

response = session.post(url=URL, json=logs)
print(response.json())

session.close()