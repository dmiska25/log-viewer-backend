
import os
from pymongo import MongoClient

def aggregate(pipeline):
    client = MongoClient(
        host=os.getenv('MONGO_HOST')
    )
    db = client['log-storage']
    logs = db['logviewerapp_log']

    result = logs.aggregate(pipeline)
    client.close()
    return result