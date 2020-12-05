from fields import parser_field

from mongoengine.fields import *
from flask_restful import reqparse

NUMBER_FILTER = [
    'ne',
    'lt' ,
    'lte',
    'gt',
    'gte'
]

STRING_FILTER = [
    'exact',
    'iexact' ,
    'contains' ,
    'icontains' ,
    'startswith' ,
    'istartswith' ,
    'endswith' ,
    'iendswith' ,
    'match'
]

ARRAY_FILTER = [
    'in',
    'nin',
    'all',
]

ARRAY_NUMBER_FILTER = [
    'size'
]

def field_filter(name, field):
    result = []
    if isinstance(field, (StringField, EmailField)):
        for key in STRING_FILTER:
            result.append(parser_field(name+'__'+key, field))
        return result
    if isinstance(field, (IntField, LongField, FloatField, DecimalField)):
        for key in NUMBER_FILTER:
            result.append(parser_field(name+'__'+key, FloatField()))
        return result
    if isinstance(field, ListField):
        for key in ARRAY_FILTER:
            result.append(parser_field(name+'__'+key, field))
        for key in ARRAY_NUMBER_FILTER:
            result.append(parser_field(name+'__'+key, IntField))
        return result
    return []