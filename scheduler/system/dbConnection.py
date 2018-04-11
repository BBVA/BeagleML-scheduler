"""
Copyright 2018 Banco Bilbao Vizcaya Argentaria, S.A.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# coding: utf-8

"""
Module for the db connection. Now the connection is with a MongoDB.

Find more info about pymongo in:
https://docs.mongodb.com/getting-started/python/
http://api.mongodb.com/python/current/index.html
"""
import time
import logging

from pymongo import MongoClient


class DBConnector:
    """Connects with ONLY ONE db and perform operation on it."""

    def __init__(self, db_url, db_port, db_name, user, password):
        self.logger = logging.getLogger("SCHEDULER")
        self.logger.info(
            'DATABASE: mongodb://' + user + ':' + password + '@' + db_url + ':' + db_port + '/' + db_name)
        client = MongoClient(
            'mongodb://' + user + ':' + password + '@' + db_url + ':' + db_port + '/' + db_name)
        self.db = client[db_name]

        self.connect()
        self.initialize_db()

    def connect(self):
        """
        Connect with the db.
        The connection with the db is tested creating a empty collection.
        10 retries are tried before it fails.
        """
        cont = 0
        while cont < 10:
            try:
                self.create_collection("__test_connection")
            except Exception:
                self.logger.warning('NO DATABASE CONNECTION')
                cont += 1
                time.sleep(5)
            else:
                self.logger.info('Database successfully connected')
                break
        if cont is 10:
            self.logger.critical('FAILED TO CONNECT THE DATABASE')

    def initialize_db(self):
        """Create collections and documents."""
        # Create needed collections
        self.create_collection('projects')
        self.create_collection('experiments')
        self.create_collection('queue')
        self.create_collection('running')
        self.create_collection('results')
        self.create_collection('models')
        self.create_collection('system')
        self.create_collection('_lastState')
        # Create needed documents
        if self.get_number_documents('queue') == 0:
            self.save_document({'queue': []}, 'queue')
            self.logger.debug('Needed to create new document for queue')
        if self.get_number_documents('running') == 0:
            self.save_document({'running': []}, 'running')
            self.logger.debug('Needed to create new document for running list')
        if self.get_number_documents('system') == 0:
            self.save_document({'experiments_limit': 1, 'running': False}, 'system')
            self.logger.debug('System parameters initialized in DDBB.')
        if self.get_number_documents('_lastState') == 0:
            self.save_document({'name': '_lastState'}, '_lastState')
            self.logger.debug('Needed to create new document for _lastState')

    def create_collection(self, coll_name):
        """Create the collection. Return True if succed or False if fail."""
        coll_names = self.db.collection_names()
        if coll_name not in coll_names:
            self.db.create_collection(coll_name)
            return True
        else:
            return False

    def save_document(self, doc, coll_name):
        """
        Save the document in the database.
        It is saved in the collection with the name specified in coll_name.
        Doc, is in a python dic form. Return the id as a ObjectID.
        """
        try:
            inserted_id = self.db[coll_name].insert_one(doc).inserted_id
        except Exception as e:
            self.logger.debug(str(e))
        return inserted_id if inserted_id else False

    def get_document(self, doc_query, coll_name, projection=None):
        """Return the document in a python dic form."""
        result = self.db[coll_name].find_one(doc_query)
        # TODO: projection (optional):
        # a list of field names that should be returned in the result set or a
        # dict specifying the fields to include or exclude.
        # If projection is a list “_id” will always be returned.
        # Use a dict to exclude fields from the result
        # (e.g. projection={‘_id’: False})
        return result if result else False

    def get_all_documents(self, coll_name):
        """Get all the documents from a collection."""
        cursor = self.db[coll_name].find({})
        all_documents = []
        for document in cursor:
            all_documents.append(document)
        return all_documents

    def get_all_ids(self, coll_name):
        """Get all ids from a collection."""
        return self.db[coll_name].distinct('_id')

    def delete_document(self, doc_query, coll_name):
        """Delete the first document that matches the query."""
        self.db[coll_name].delete_one(doc_query)

    def delete_documents(self, doc_query, coll_name):
        """Delete all documents that matches the query."""
        self.db[coll_name].delete_many(doc_query)

    def delete_all_documents(self, coll_name):
        """Delete all documents from a collection."""
        self.db[coll_name].delete_many({})

    def update_document(self, doc_query, doc_update, coll_name):
        """Update the first document matched with the query."""
        try:
            updated = self.db[coll_name].update_one(doc_query, {'$set': doc_update})
        except Exception as e:
            self.logger.debug(str(e))
        return updated.matched_count if updated else False

    def push_document(self, doc_query, key, element, coll_name, first=False):
        """Insert an element in a list in a document."""
        if first:
            self.db[coll_name].update_one(
                doc_query,
                {'$push': {key: {'$each': [element], '$position': 0}}})
        else:
            self.db[coll_name].update_one(
                doc_query, {'$push': {key: element}})

    def pop_document(self, doc_query, key, coll_name, last=False):
        """Return and remove the first element in a list in a documment."""
        result = self.db[coll_name].find_one_and_update(
            doc_query, {'$pop': {key: -1}})
        try:
            if not last:
                return result[key].pop(0)
            else:
                return result[key].pop()
        except IndexError:
            return False

    def pull_document(self, doc_query, key, element, coll_name):
        """Remove the element specified in a list inside a document."""
        self.db[coll_name].update_one(doc_query, {'$pull': {key: element}})

    def get_number_documents(self, coll_name, query={}):
        """Return the number of documents in a collection."""
        num = self.db[coll_name].find(query).count()
        return num

    def get_document_paginate_list(self, coll_name, query, key, start, end):
        """Return a document with a list paginated."""
        # self.logger.info('Pagination: ' + str(start) + '-' + str(end))
        return self.db[coll_name].find_one(
            query, {key: {'$slice': [start, end]}, '_id': 0})

    def count_array_document(self, coll_name, query, key):
        """Return the number of elements in an array inside a document."""
        # TODO: Check a better way to do this. Returns all the array and
        # then counts it. Very very cutre
        return len(self.get_document(coll_name=coll_name, doc_query=query)[key])

    def is_in_list(
            self, doc_query, key, element_key, element_value, coll_name):
        """Check if a element is in a list inside a document."""
        result = self.db[coll_name].find_one(doc_query)

        return any(d[element_key] == element_value for d in result[key])

if __name__ == "__main__":
    db_url = '172.30.23.2'
    db_port = '27017'
    db_name = 'automodeling'
    user = 'user0LT'
    password = 'P4fQMKF7yERFddXu'
    db = DBConnector(db_url, db_port, db_name, user, password)
