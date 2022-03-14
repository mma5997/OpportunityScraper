import csv
import json
import firebase_admin
import google.cloud
from firebase_admin import credentials, firestore
from datetime import datetime
from dateutil import parser

CRED = credentials.Certificate("./Secret/serviceAccountKey.json")
APP = firebase_admin.initialize_app(CRED)

store = firestore.client()

# file_path = "C:\\Users\\mautade\\Git_WS\\OpportunityScraperRepo\\Files\\ScrapedJobs.csv"
FILE_PATH = "./Files/ScrapedJobs.csv"
COLLECTION_NAME = "opportunity"

DATE_VAR = list(["createdOn", "expiresOn", "opportunityDate", "updatedOn"])


def batch_data(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


data = []
headers = []
with open(FILE_PATH) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            for header in row:
                headers.append(header)
            line_count += 1
        else:
            obj = {}
            for idx, item in enumerate(row):
                if headers[idx] in DATE_VAR:
                    item = parser.parse(item)
                obj[headers[idx]] = item
            if len(obj) > 0:
                data.append(obj)
            line_count += 1
    print(f'#### Processed {line_count} lines ####')


for batched_data in batch_data(data, 499):
    batch = store.batch()
    for data_item in batched_data:
        doc_ref = store.collection(COLLECTION_NAME).document()
        batch.set(doc_ref, data_item)
    batch.commit()

print('#### Done ####')
