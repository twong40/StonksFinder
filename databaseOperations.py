import pymongo
from pymongo import MongoClient
from credentials import mongodbConnection, mongodbPassword

def createClient():
    client = MongoClient(mongodbConnection.replace("<password>", mongodbPassword))
    return client["database-1"]

def insertOne(db, post):
    search_data = db.search_data
    return search_data.insert_one(post).inserted_id

def insertMany(db, posts):
    search_data = db.search_data
    return search_data.insert_many(posts).inserted_ids



