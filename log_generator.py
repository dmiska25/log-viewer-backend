from datetime import datetime, timedelta
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

notices = [
    'logon',
    'logoff',
]

user_ids = []
# seed the users
for i in range(600):
    user_ids.append(fake.isbn13())


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
    def __init__(self, error, **kwargs) -> None:
        super().__init__(**kwargs)
        self.error = error

    def getDefaultArgs():
        default_args = {
            "error": {"traceback": "Examples"},
            **BaseLog.getDefaultArgs()
        }
        default_args.update({'type': 'E'})
        return default_args

    def generate():
        return ErrorLog(**ErrorLog.getDefaultArgs())
        
class UserLog(BaseLog):
    last_given_time = datetime.now()
    last_given_notice = 'logoff'
    last_given_session_id = None
    last_given_user_id = None
  
    def getNotice():
        if UserLog.last_given_notice == 'logon':
            UserLog.last_given_notice = 'logoff'
            return UserLog.last_given_notice
        UserLog.last_given_notice = 'logon'
        return UserLog.last_given_notice

    def getTime():
        if UserLog.last_given_notice == 'logon':
            return fake.date_time_between_dates(UserLog.last_given_time, UserLog.last_given_time + timedelta(hours=5)).isoformat(sep='T', timespec='auto')
        UserLog.last_given_time = fake.past_datetime()
        return UserLog.last_given_time.isoformat(sep='T', timespec='auto')

    def getSessionId():
        if UserLog.last_given_notice == 'logon':
            return UserLog.last_given_session_id
        UserLog.last_given_session_id = fake.isbn13()
        return UserLog.last_given_session_id

    def getUserId():
        if UserLog.last_given_notice == 'logon':
            return UserLog.last_given_user_id
        UserLog.last_given_user_id = random.choice(user_ids)
        return UserLog.last_given_user_id

    def __init__(self, details, **kwargs) -> None:
        super().__init__(**kwargs)
        self.details = details

    def getDefaultArgs():
        default_args = {**BaseLog.getDefaultArgs()}
        default_args.update({
            'type': 'I',
            'severity': 'L', 
            'service_name': 'user device',
            'timestamp': UserLog.getTime(), 
            "details": {
                "session_id": UserLog.getSessionId(), 
                "user_id": UserLog.getUserId(),
                "notice": UserLog.getNotice(),
            },
        })
        return default_args

    def generate():
        return UserLog(**UserLog.getDefaultArgs())

# define generation and quantities
generation = {
    UserLog: 1000,
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
session.close()