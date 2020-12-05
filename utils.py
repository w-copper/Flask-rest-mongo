from flask import abort
from flask.views import MethodView
from flask_restful import Resource, reqparse
from flask_restful.reqparse import Argument
from mongoengine import ( 
    DictField, StringField, ReferenceField, ListField, IntField, BooleanField, FloatField, ObjectIdField,
    EmailField, GeoJsonBaseField, PointField
)
from bson.objectid import ObjectId
import json


def get_ref_instance(field, id, raise_error = True):
    assert isinstance(field, ReferenceField)
    document = field.document_type
    assert document is not None
    idf = document._meta['id_field']
    if  isinstance(document._fields[idf], ObjectIdField):
        id = ObjectId(id)
    obj = document.objects(**{idf:id}).first()
    assert obj is not None
    return obj

def fix_complex_field(field, value):
    if field is None or isinstance(field, (StringField, IntField, BooleanField, FloatField, DictField) ):
        return value
    if isinstance(field, (GeoJsonBaseField, PointField)):
        return json.loads(value)
    if isinstance(field, ReferenceField):
        return get_ref_instance(field, value)
    if isinstance(field, (ListField,)):
        fs = []
        for v in value:
            fs.append(fix_complex_field(field.field, v))
        return fs

def fix_complex_args(field, value):
    if field is None or isinstance(field, (StringField, IntField, BooleanField, FloatField, DictField) ):
        return value
    if isinstance(field, ReferenceField):
        return ObjectId(value)
    if isinstance(field, (ListField,)):
        fs = []
        for v in value:
            fs.append(fix_complex_args(field.field, v))
        return fs

FIELD_TO_PYTHON = {
    IntField:int,
    FloatField:float,
    ListField:list,
    ReferenceField:str,
    StringField:str,
    BooleanField:bool,
    GeoJsonBaseField:dict
}

NUMBER_FILTERS = [
    'gt','gte','lt', 'lte', 'ne'
]
STRING_FILTERS = [
    'exact', 'iexact', 'contains', 'icontains'
]
ARRAY_FILTERS = [
    'in', 'nin'
]

def fix_parser(name, field, has_filter=False):
    args = {
        'name':name,
        'type':None,
        'location':('json', 'args'),
        'default':None
    }
    filter_args = []
    maps = {}
    if isinstance(field, IntField):
        args['type'] = int
        maps[name] = field
        if has_filter:
            for t in NUMBER_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':int,
                        'location':('json', 'args')
                    }
                )
                maps[name+'__'+t] = field
            for t in ARRAY_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':list,
                        'location':('json')
                    }
                )
                maps[name+'__'+t] = field
    elif isinstance(field, FloatField):
        args['type'] = float
        maps[name] = field
        if has_filter:
            for t in NUMBER_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':float,
                        'location':('json', 'args')
                    }
                )
                maps[name+'__'+t] = field
            for t in ARRAY_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':list,
                        'location':('json')
                    }
                )
                maps[name+'__'+t] = field
    elif isinstance(field, BooleanField):
        args['type'] = bool
        maps[name] = field
    elif isinstance(field, StringField):
        args['type'] = str
        maps[name] = field
        if has_filter:
            for t in STRING_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':str,
                        'location':('json', 'args')
                    }
                )
                maps[name+'__'+t] = field
            for t in ARRAY_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':list,
                        'location':('json')
                    }
                )
                maps[name+'__'+t] = field
    elif isinstance(field, ReferenceField):
        args['type'] = str
        maps[name] = field
        if has_filter:
            for t in ARRAY_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':list,
                        'location':('json')
                    }
                )
                maps[name+'__'+t] = field
    elif isinstance(field, ListField):
        args['type'] = list
        args['location'] = ('json')
        maps[name] = field
        if has_filter:
            for t in ARRAY_FILTERS:
                filter_args.append(
                    {
                        'name':name+'__'+t,
                        'type':list,
                        'location':('json')
                    }
                )
                maps[name+'__'+t] = field
    elif isinstance(field, (GeoJsonBaseField, PointField)):
        args['type'] = str
        args['location'] = 'json'
        maps[name] = field
    else:
        return None,None

    argument = Argument(**args)
    filter_arguments = []
    for a in filter_args:
        filter_arguments.append(Argument(**a))
    return [ argument, *filter_arguments ], maps

class MixsListCreate(MethodView):
    model = None
    order = None
    permission_check = None
    exclude = []
    parser = None
    
    def __init__(self):
        self._filters = []
        self._parser = None
        self._arg_map = {}
        self.init_parser()

    def init_parser(self):
        self._parser = reqparse.RequestParser()
        self._parser.add_argument('pageSize', type=int, default=0)
        self._parser.add_argument('page', type=int, default=0)
        fields = self.model._fields
        id_key = self.get_id_field()
        # 暂时只支持字符串和objectid类型的id
        self._parser.add_argument('id', dest=id_key, type=str)
        for key in fields:
            if key == id_key:
                continue
            if key in self.exclude:
                continue
            args, maps = fix_parser(key, fields[key], True)
            if args is None:
                continue
            for arg in args:
                self._parser.add_argument(arg)
            for m in maps:
                if m not in self._arg_map:
                    self._arg_map[m] =maps[m]
                self._filters.append(m)
        if self.parser is not None:
            for arg in self.parser.args:
                self._parser.remove_argument(arg.name).add_argument(arg)
                self._filters.append(arg.name)

    def permission_checks(self, method:str):
        if self.permission_check is None:
            return
        if isinstance(self.permission_check, (list, tuple)):
            for pc in self.permission_check:
                pc()
        if isinstance(self.permission_check, dict):
            pcs = self.permission_check.get(method.lower(), [])
            for pc in pcs:
                pc()

    def get_filter(self):
        return {}

    def get_query_set(self):
        assert self.model is not None
        return self.model.objects()

    def get_id_field(self):
        assert self.model is not None
        return self.model._meta['id_field']

    def create_obj_post(self, obj):
        pass

    def get_dict_obj(self, str_or_dict):
        if isinstance(str_or_dict, str):
            return json.loads(str_or_dict)
        return str_or_dict

    def get(self):
        try:
            self.permission_checks('get')
            filters = {}
            args = self._parser.parse_args()
            # print(args)
            for key in self._filters:
                if args[key] is None:
                    continue
                if key not in self._arg_map:
                    filters[key] = args[key]
                else:
                    filters[key] = fix_complex_args(self._arg_map[key], args[key])
                      
            user_filter = self.get_filter()
            for key in user_filter:
                filters[key] = user_filter[key]
            
            order = self.get_id_field() if self.order is None else self.order
            query_set =  self.model.objects(**filters).order_by(order).exclude(*self.exclude)
            pageSize = 0
            
            if hasattr(args, 'pageSize'):
                pageSize = args.pageSize if args.pageSize is not None else 0


            if pageSize > 0:
                total = query_set.count()
                pageCount = total // pageSize + 1
                page = args['page']
                data = query_set[page * pageSize: (page+1) * pageSize]
                return {
                    'total':total,
                    'pageCount':pageCount,
                    'page':page,
                    'data': list(self.get_dict_obj(o.to_json()) for o in data)
                }
            else:
                data = query_set
                return {
                    'data': list(self.get_dict_obj(o.to_json()) for o in data)
                }
        except Exception as e:
            print(str(e))
            return { 'msg':str(e), 'error':1 }, 400
        
    
    def post(self):
        self.permission_checks('post')
        fields = self.model._fields
        try:
            args = self._parser.parse_args()
            data = {}
            for field in fields:
                if field not in args or args[field] is None:
                    continue
                data[field] = fix_complex_field(fields[field], args[field])
            print(data)
            obj = self.model(**data)
            obj.save()
            self.create_obj_post(obj)
            data = obj.to_json()
            if isinstance(data, str):
                return json.loads(data)
            return obj.to_json()
        except Exception as e:
            print(e)
            return { 'error': 1, 'msg': str(e) }, 400

class MixsDetail(MethodView):
    '''
    实现根据id获取详情、对其进行删除、更新
    '''
    model = None
    parser = None
    permission_check = None
    exclude = []
    read_only = []

    def __init__(self):
        self._parser = None
        self.init_parser()

    def permission_checks(self, method:str):
        if self.permission_check is None:
            return
        if isinstance(self.permission_check, (list, tuple)):
            for pc in self.permission_check:
                pc(self.obj)
        if isinstance(self.permission_check, dict):
            pcs = self.permission_check.get(method.lower(), [])
            for pc in pcs:
                pc(self.obj)

    def get_id_field(self):
        assert self.model is not None
        return self.model._meta['id_field']

    def init_parser(self):
        self._parser = reqparse.RequestParser()
        fields = self.model._fields
        id_key = self.get_id_field()
        # 暂时只支持字符串和objectid类型的id
        self._parser.add_argument('id', dest=id_key, type=str, location=('json', 'args'))

        for key in fields:
            if key  == id_key:
                continue
            if isinstance(fields[key], (StringField, ReferenceField, PointField)):
                self._parser.add_argument(key, type=str, location=('json', 'args'))
            elif isinstance(fields[key], (ListField,)):
                self._parser.add_argument(key, type=list, location=('json'))
            elif isinstance(fields[key], (IntField,)):
                self._parser.add_argument(key, type=int, location=('json', 'args'))
            elif isinstance(fields[key], (FloatField,)):
                self._parser.add_argument(key, type=float, location=('json', 'args'))
            elif isinstance(fields[key], BooleanField):
                self._parser.add_argument(key, type=bool, location=('json', 'args'))
        if self.parser is not None:
            for arg in self.parser.args:
                self._parser.remove_argument(arg.name).add_argument(arg)
    def get_update_field(self):
        id_field = self.get_id_field()
        fields = self.model._fields
        return dict( (key, fields[key]) for key in fields if (key != id_field) and (key not in self.read_only) )

    def get_object(self):
        id_field = self.get_id_field()
        args = self._parser.parse_args()
        obj = self.model.objects(**{ id_field:args[id_field] }).first()
        if obj is None:
            abort(404)
        self.obj = obj
        return obj
    
    def get(self):
        obj = self.get_object()
        self.permission_checks('get')
        
        data = obj.to_json()
        if isinstance(data, str):
            data = json.loads(data)
        for key in self.exclude:
            del data[key]
        return data

    def patch(self):
        obj = self.get_object()
        self.permission_checks('patch')
        args = self._parser.parse_args()
        print(args)
        update_fields = self.get_update_field()
        for key in update_fields:
            if args[key] is None:
                continue
            data = fix_complex_field(update_fields[key], args[key])
            obj[key] = data
            
        obj.save()
        data = obj.to_json()
        if isinstance(data, str):
            data = json.loads(data)
        for key in self.exclude:
            if key in data:
                del data[key]
        return data

    def put(self):
        return self.patch()
        
    def delete(self):
        obj = self.get_object()
        self.permission_checks('delete')
        obj.delete()
        return { 'msg': 'ok!' }