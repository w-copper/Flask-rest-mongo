import json

from flask import request
from flask_restful import abort, reqparse

from .fields import parser_field
from .filters import field_filter


class Mixs(object):
    """
    docstring
    """
    document = None
    permissions = {}
    page = None

    def __init__(self):
        self._parser = None
        self._arg_map = {}
        self._page_parser = None
        self._filter_parser = None
        self._init_parser()

    @property
    def _fields(self):
        return self.document._fields

    def get_document(self):
        return self.document

    @property
    def _id(self):
        return self.document._meta['id_field']

    def get_object(self):
        args = self._valid_args(self._parser)
        if self._id not in args:
            abort(400, msg='%s is required'%self._id, error=1)
        obj = self.document.objects(**{self._id: args[self._id]}).first()
        if obj is None:
            abort(404, msg='cound not find object with %s=%s'%(self._id, args[self._id]), error=1)
        return obj

    def _valid_args(self, parser):
        args = parser.parse_args()
        print(args)
        def f(k): return k[1] is not None
        return dict(filter(f, args.items()))

    def _check_permission(self, name: str, *args):
        if isinstance(self.permissions, dict):
            func = self.permissions.get(name.lower(), None)
            if func is not None:
                if isinstance(func, list):
                    for f in func:
                        f(*args)
            return
        if isinstance(self.permissions, list):
            for f in self.permissions:
                f(*args)
            return
        if self.permissions is not None:
            self.permissions(*args)

    def _init_parser(self):
        self._init_fields_parser()
        self._init_filter_parser()
        self._init_page_parser()

    def _init_fields_parser(self):
        self._parser = reqparse.RequestParser()
        fields = self._fields
        for key in fields:
            self._parser.add_argument(
                parser_field(name=key, field=fields[key]))

    def _init_filter_parser(self):
        pass

    def _init_page_parser(self):
        pass

    def _obj_to_json_dict(self, obj):
        s = obj.to_json()
        if isinstance(s, str):
            return json.loads(s)
        return s


class MixList(Mixs):
    """
    docstring
    """
    page = True
    page_key = 'page'
    page_size_key = 'page_size'
    page_size_default = 10
    order_key = None
    # order_default = 'id'
    exclude = []
    max_count = 0

    @property
    def _filter_maps(self):
        pass

    def _init_page_parser(self):
        self._page_parser = reqparse.RequestParser()
        self._page_parser.add_argument(self.page_key, type=int, default=0)
        self._page_parser.add_argument(
            self.page_size_key, type=int, default=self.page_size_default)

    def _init_filter_parser(self):
        self._filter_parser = reqparse.RequestParser()
        fields = self._fields
        for key in fields:
            for aug in field_filter(key, fields[key]):
                self._filter_parser.add_argument(aug)

    def get_filter(self):
        pass

    def _get_filters(self):
        filters = self._valid_args(self._filter_parser)
        filter_rq = {}
        for key in filters:
            filter_rq[key] = filters[key]
        user_filter_parser = self.get_filter()
        if user_filter_parser is None:
            pass
        else:
            user_filters = self._valid_args(user_filter_parser)
            for key in user_filters:
                filter_rq[key] = user_filters[key]
        return filter_rq

    def get(self):
        self._check_permission('get')
        filters = self._get_filters()
        document = self.get_document()
        docs = document.objects(**filters).exclude(*self.exclude)
        if self.order_key is not None:
            order_by = self.order_key
            if isinstance(self.order_key, str):
                order_by = (order_by,)
            docs = docs.order_by(*order_by)
        if self.page:
            pages = self._page_parser.parse_args()
            page = pages[self.page_key]
            size = pages[self.page_size_key]
            total = docs.count()
            start = page * size
            end = page * size + size
            if start >= total:
                return {'total': total, 'data': [], self.page_key: page, self.page_size_key: size}
            if end >= total:
                end = total
            docs = docs[start:end]

            data_list = []
            for obj in docs:
                data_list.append(self._obj_to_json_dict(obj))

            return {'total': total, 'data': data_list, self.page_key: page, self.page_size_key: size}
        if self.max_count > 0:
            if docs.count() > self.max_count:
                docs = docs[:self.max_count]
        data_list = []
        for obj in docs:
            data_list.append(self._obj_to_json_dict(obj))

        return {'data': data_list}


class MixCreate(Mixs):
    """
    docstring
    """
    use_json = False

    def create_obj(self):
        if self.use_json:
            data = request.json
            obj = self.document.from_json(data)
            obj.save()
        else:
            try:
                data = self._valid_args(self._parser)
                obj = self.document(**data)
                obj.save()
            except Exception as e:
                abort(400, msg=str(e), error=1)
        return obj

    def post(self):
        self._check_permission('post')
        obj = self.create_obj()
        return self._obj_to_json_dict(obj)


class MixListCreate(MixCreate, MixList):
    """
    docstring
    """
    pass


class MixRetrial(Mixs):
    """
    docstring
    """

    def get(self):
        self._check_permission('get')
        obj = self.get_object()
        return self._obj_to_json_dict(obj)


class MixUpdate(Mixs):
    """
    docstring
    """

    def put(self):
        self._check_permission('put')
        obj = self.get_object()
        update_data = self._valid_args(self._parser)
        obj.update(**update_data)
        obj.save()
        return self._obj_to_json_dict(obj)

    def patch(self):
        self._check_permission('patch')
        return self.put()


class MixDelete(Mixs):
    """
    docstring
    """

    def delete(self):
        self._check_permission('delete')
        obj = self.get_object()
        obj.delete()
        return {'msg': 'ok'}


class MixRetrialUpdate(MixRetrial, MixUpdate):
    pass


class MixRetrialDelete(MixRetrial, MixDelete):
    pass


class MixUpdateDelete(MixUpdate, MixDelete):
    pass


class MixRetrialUpdateDelete(MixRetrial, MixUpdate, MixDelete):
    pass
