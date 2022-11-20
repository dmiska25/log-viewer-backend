
from pymongo import MongoClient

def aggregate(pipeline):
    client = MongoClient()
    db = client['log-storage']
    logs = db['logviewerapp_log']

    result = logs.aggregate(pipeline)
    client.close()
    return result