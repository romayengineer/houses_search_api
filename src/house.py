from flask import request, jsonify

from src.conf import db
from src.zipwho import get_zips_by_demographics

class House(db.Model):
    id = db.Column(db.String(120), primary_key=True, unique=True)
    brokered_by = db.Column(db.String(120))
    status = db.Column(db.String(30))
    price = db.Column(db.Float)
    bed = db.Column(db.Integer)
    bath = db.Column(db.Integer)
    acre_lot = db.Column(db.Float)
    street = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    zip_code = db.Column(db.String(120))
    house_size = db.Column(db.Float)
    prev_sold_date = db.Column(db.String(120))
    # code from mapping
    state_code = db.Column(db.String(10))
    # calculated columns
    price_per_acre = db.Column(db.Float)
    price_per_sq_ft = db.Column(db.Float)

house_attrs = [
    'acre_lot',
    'bath',
    'bed',
    'brokered_by',
    'city',
    'house_size',
    'id',
    'prev_sold_date',
    'price',
    'price_per_acre',
    'price_per_sq_ft',
    'state',
    'state_code',
    'status',
    'street',
    'zip_code',
]

def house_to_dict(house):
    return {
        k: getattr(house, k) for k in house_attrs
    }

def filter_by_range(args, query, name, type):
    min_value = args.get(f'min_{name}', type=type)
    max_value = args.get(f'max_{name}', type=type)

    if min_value is not None:
        query = query.filter(getattr(House, name) >= min_value)
    if max_value is not None:
        query = query.filter(getattr(House, name) <= max_value)

    return query

def filter_by_exact_match(args, query, name, type):
    value = args.get(name, type=type)

    if value is not None:
        query = query.filter(getattr(House, name) == value)

    return query

def get_house_by_property(args):
    query = House.query

    status = args.get('status', type=str)
    if not status:
        return jsonify({"error": "The 'status' argument is required."}), 400
    query = query.filter(House.status == status)

    query = filter_by_range(args, query, "price", float)
    query = filter_by_range(args, query, "bed", int)
    query = filter_by_range(args, query, "bath", int)
    query = filter_by_range(args, query, "acre_lot", int)
    query = filter_by_range(args, query, "price_per_acre", int)
    query = filter_by_range(args, query, "house_size", int)
    query = filter_by_range(args, query, "price_per_sqft", int)

    query = filter_by_exact_match(args, query, "city", type=str)
    query = filter_by_exact_match(args, query, "state", type=str)
    query = filter_by_exact_match(args, query, "zip_code", type=str)
    # state_code is required for demographics search
    query = filter_by_exact_match(args, query, "state_code", type=str)

    # as requirements only filters by demographics if state_code is given
    if args.get("state_code") is not None:
        zips = get_zips_by_demographics(args)
        query = query.filter(House.zip_code.in_(zips))

    # supports pagination
    page = args.get('page', 1, type=int)
    per_page = args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, max_per_page=500)

    return pagination
