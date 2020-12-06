# For test

from flask import Flask
from flask_mongoengine import MongoEngine
from mongoengine import fields
from flask_restful import Resource, Api
from flask_rest_mongo.mix import *
import mongoengine

class Config(object):

    ENV = 'development'
    SERVER_NAME = '127.0.0.1:7788'
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'flaskTest',
        'host': '127.0.0.1',
        'port': 27017
    }

if __name__ == "__main__":
    app = Flask(__name__)
    db = MongoEngine()
    api = Api()
    app.config.from_object(Config())
    

    class UserTest(db.DynamicDocument):
        username = fields.StringField(primary_key=True)
        email = fields.EmailField()
        password = fields.StringField()
        def to_json(self):
            return {
                'username':self.username,
                'email':self.email
            }

    class DataTest(db.DynamicDocument):
        data = fields.DictField()
        list_data = fields.ListField()
        def to_json(self, *args, **kwargs):
                return {
                    'id':str(self.id),
                    'data':self.data,
                    'list':self.list_data
                }

    class TestDocument(db.DynamicDocument):
        user = fields.ReferenceField(UserTest, reverse_delete_rule=mongoengine.CASCADE, required=True)
        data_list = fields.ListField(fields.ReferenceField(DataTest))
        count = fields.IntField()
        factor = fields.FloatField()
        
    
    class UserListCreate(Resource, MixListCreate):
        document = UserTest
        exclude = ['password']
        page = True
    api.add_resource(UserListCreate, '/user/')
    class UserDetail(Resource, MixRetrialUpdateDelete):
        document = UserTest
        exclude = ['password']
    api.add_resource(UserDetail, '/user/detail/')

    class DataListCreate(Resource, MixListCreate):
        document = DataTest
        page = True
    api.add_resource(DataListCreate, '/data/')
    class DataDetail(Resource, MixRetrialUpdateDelete):
        document = DataTest
    api.add_resource(DataDetail, '/data/detail/')

    class TestDocumentListCreate(Resource, MixListCreate):
        document = TestDocument
        page = True
    api.add_resource(TestDocumentListCreate, '/test/')
    class TestDocumentDetail(Resource, MixRetrialUpdateDelete):
        document = TestDocument
    api.add_resource(TestDocumentDetail, '/test/detail/')


    db.init_app(app)
    api.init_app(app)

    app.run()
