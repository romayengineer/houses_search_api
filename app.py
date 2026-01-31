import os
import csv
import hashlib
import sqlite3
import requests
from lxml import html
from urllib.parse import urlencode
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from playwright.sync_api import sync_playwright

state_map = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

class Demographic(db.Model):
    zip_code = db.Column(db.String(10), primary_key=True, unique=True)
    median_income = db.Column(db.Float)
    population = db.Column(db.Float)
    median_age = db.Column(db.Float)

@app.cli.command("init-db")
def init_db():
    """Clear existing data and create new tables."""
    db.create_all()
    print("Database initialized!")

def to_float(number):
    try:
        return float(number)
    except ValueError:
        return None

def db_optimization(cursor):
    # Disables rollback log
    cursor.execute("PRAGMA journal_mode = OFF;")
    # Doesn't wait for disk write confirmation
    cursor.execute("PRAGMA synchronous = OFF;")
    # Uses 1GB of RAM for cache
    cursor.execute("PRAGMA cache_size = -1000000;")
    # Prevents other apps from touching DB
    cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")

def insert_house(cursor, buffer):
    cursor.executemany(
        "INSERT OR IGNORE INTO house (brokered_by, status, price, bed, bath, acre_lot, street, city, state, zip_code, house_size, prev_sold_date, state_code, price_per_acre, price_per_sq_ft, id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
        buffer
    )

@app.cli.command("import-csv")
def import_csv():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    db_optimization(cursor)

    csv_file_path = os.path.join(basedir, 'realtor-data.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: {csv_file_path} not found.")
        return

    with open(csv_file_path, mode='r') as file:
        # skip header
        file.readline()

        count_added = 0
        in_batch = 0
        batch_size = 100000
        buffer = []

        for raw_line in file:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            row_hash = hashlib.sha256(raw_line.encode('utf-8')).hexdigest()

            columns = next(csv.reader([raw_line]))

            state = columns[8]
            state_code = state_map.get(state, "")
            columns.append(state_code)
            
            price = to_float(columns[2])
            if price is None or price <= 0:
                continue
            columns[2] = price

            acre_lot = to_float(columns[5]) or 0
            columns[5] = acre_lot
            price_per_acre = 0 if acre_lot == 0 else price / acre_lot
            columns.append(price_per_acre)

            house_size = to_float(columns[10]) or 0
            columns[10] = house_size
            price_per_sq_ft = 0 if house_size == 0 else price / house_size
            columns.append(price_per_sq_ft)

            columns.append(row_hash)
            buffer.append(columns)

            count_added += 1
            in_batch += 1
            if in_batch == batch_size:
                insert_house(cursor, buffer)
                conn.commit()
                print("completed %.2f %%" % (100 * count_added / 2300000))
                in_batch = 0
                buffer = []

        if buffer:
            insert_house(cursor, buffer)
            conn.commit()
            print("completed %.2f %%" % (100 * count_added / 2300000))
            in_batch = 0
            buffer = []

        print(f"Import finished: {count_added} added")

@app.cli.command("download-csv")
def download_s3_csv():
    url = "https://getgloby-realtor-challenge.s3.us-east-1.amazonaws.com/realtor-data.csv"
    dest_path = "realtor-data.csv"
    print(f"Downloading {url}...")
    # stream=True allows us to download the file in pieces
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    print(f"Download complete: {dest_path}")

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

@app.route('/properties', methods=['GET'])
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

    # supports pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, max_per_page=500)

    #TODO add demographic search parameters
    # - `min_population`
    # - `max_population`
    # - `min_median_income`
    # - `max_median_income`
    # - `min_median_age`
    # - `max_median_age`

    return jsonify({
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page,
        "results": [
            house_to_dict(h) for h in pagination.items
        ]
    })

@app.route('/properties/<string:house_id>', methods=['GET'])
def get_property_by_id(house_id):
    house = House.query.get(house_id)

    if not house:
        return jsonify({"error": "Property not found"}), 404

    #TODO add zip info
    # "zip_info": {
    #    "median_income": ...,
    #    "population": ...,
    #    "median_age": ...
    # }

    return jsonify(house_to_dict(house))

table_labels = [
    "Median Income",
    "Cost Of Living Index",
    "Median Mortgage To Income Ratio",
    "Owner Occupied Homes",
    "Median Rooms In Home",
    "College Degree",
    "Professional",
    "Population",
    "Average Household Size",
    "Median Age",
    "Male To Female Ratio",
    "Married",
    "Divorced",
    "White",
    "Black",
    "Asian",
    "Hispanic Ethnicity",
]

table_attributes = [
    label.lower().replace(" ", "_") for label in table_labels
]

def parse_table(table_cells):
    # there are 17 attributes (rows in the table)
    # and there are 3 columns for each
    # therefore there are 51 cells in total
    cells_count = len(table_cells)
    if cells_count == 51:
        i = 1
        parsed = []
        for number in table_cells:
            # we only care about the second column
            # and the cells that falls into the second column
            # is always 2 + 3n for example 2, 5, 8, 11
            if (i - 2) % 3 == 0:
                parsed.append(number)
            i += 1
        return dict(zip(table_attributes, parsed))

@app.route('/demographics/<string:zip_code>', methods=['GET'])
def get_demographic(zip_code):
    url_arguments = urlencode({
        "zip": zip_code,
        "mode": "zip",
    })
    full_url = f"https://zipwho.com/?{url_arguments}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(full_url)
        page.wait_for_selector("div#details_table", timeout=10000)
        table_content = page.inner_html("div#details_table")
        tree = html.fromstring(table_content)
        table_cells = tree.xpath("//td/text()")
        parsed = parse_table(table_cells)
        parsed["zip_code"] = zip_code
        return jsonify(parsed)

if __name__ == '__main__':
    app.run(debug=True)