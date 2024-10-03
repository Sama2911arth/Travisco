import os
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Absolute path to your Firebase Admin SDK JSON file
json_path = os.path.abspath("app/travisco-ca6c3-firebase-adminsdk-5phpr-a65adc8bcb.json")
cred = credentials.Certificate(json_path)
firebase_admin.initialize_app(cred)

db = firestore.client()