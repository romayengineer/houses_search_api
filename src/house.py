from flask import request, jsonify

from conf import db
from zipwho import get_zips_by_demographics

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

def house_to_dict(house):
    return {
        "id": house.id,
        "brokered_by": house.brokered_by,
        "status": house.status,
        "price": house.price,
        "bed": house.bed,
        "bath": house.bath,
        "acre_lot": house.acre_lot,
        "street": house.street,
        "city": house.city,
        "state": house.state,
        "zip_code": house.zip_code,
        "house_size": house.house_size,
        "prev_sold_date": house.prev_sold_date,
        "state_code": house.state_code,
        "price_per_acre": house.price_per_acre,
        "price_per_sq_ft": house.price_per_sq_ft,
    }

def filter_by_range(query, name, type):
    min_value = request.args.get(f'min_{name}', type=type)
    max_value = request.args.get(f'max_{name}', type=type)

    if min_value is not None:
        query = query.filter(getattr(House, name) >= min_value)
    if max_value is not None:
        query = query.filter(getattr(House, name) <= max_value)

    return query

def filter_by_exact_match(query, name, type):
    value = request.args.get(name, type=type)

    if value is not None:
        query = query.filter(getattr(House, name) == value)

    return query

def get_house_by_property():
    query = House.query

    status = request.args.get('status', type=str)
    if not status:
        return jsonify({"error": "The 'status' argument is required."}), 400
    query = query.filter(House.status == status)

    query = filter_by_range(query, "price", float)
    query = filter_by_range(query, "bed", int)
    query = filter_by_range(query, "bath", int)
    query = filter_by_range(query, "acre_lot", int)
    query = filter_by_range(query, "price_per_acre", int)
    query = filter_by_range(query, "house_size", int)
    query = filter_by_range(query, "price_per_sqft", int)

    query = filter_by_exact_match(query, "city", type=str)
    query = filter_by_exact_match(query, "state", type=str)
    query = filter_by_exact_match(query, "zip_code", type=str)
    # state_code is required for demographics search
    query = filter_by_exact_match(query, "state_code", type=str)

    # as requirements only filters by demographics if state_code is given
    if request.args.get("state_code") is not None:
        zips = get_zips_by_demographics()
        query = query.filter(House.zip_code.in_(zips))

    # supports pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, max_per_page=500)

    return pagination
