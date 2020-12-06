# Flask-REST-MongoDB

------------------------

一个用于快速构建RESTful API的辅助库，该库依赖于：
    - `Flask`
    - `Falsk-restful`
    - `MongoEngine`

## 1. 核心工具类

实现了基本的GET\POST\PUT\PATCH\DELETE方法

```python
flask_rest_mongo.mix.MixList # 实现get接口，获取批量数据
flask_rest_mongo.mix.MixCreate # 实现post接口，新建document
flask_rest_mongo.mix.MixRetrial # 实现get接口，获取单个document
flask_rest_mongo.mix.MixUpdate # 实现put与patch接口，更新document
flask_rest_mongo.mix.MixDelete # 实现delete接口，删除document
```
除此之外提供了各种组合
```python
flask_rest_mongo.mix.MixListCreate
flask_rest_mongo.mix.MixRetrialUpdate
flask_rest_mongo.mix.MixRetrialDelete
flask_rest_mongo.mix.MixUpdateDelete
flask_rest_mongo.mix.MixRetrialUpdateDelete
```

## 2. 示例

```python
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
```