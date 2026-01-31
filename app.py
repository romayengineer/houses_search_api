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
from contextlib import suppress
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

# this is what is displayed in the table
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

# these are the name used for columns
table_attributes = [
    label.lower().replace(" ", "_") for label in table_labels
]

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
    cost_of_living_index = db.Column(db.Float)
    median_mortgage_to_income_ratio = db.Column(db.Float)
    owner_occupied_homes = db.Column(db.Float)
    median_rooms_in_home = db.Column(db.Float)
    college_degree = db.Column(db.Float)
    professional = db.Column(db.Float)
    population = db.Column(db.Float)
    average_household_size = db.Column(db.Float)
    median_age = db.Column(db.Float)
    male_to_female_ratio = db.Column(db.Float)
    married = db.Column(db.Float)
    divorced = db.Column(db.Float)
    white = db.Column(db.Float)
    black = db.Column(db.Float)
    asian = db.Column(db.Float)
    hispanic_ethnicity = db.Column(db.Float)

@app.cli.command("init-db")
def init_db():
    """Clear existing data and create new tables."""
    db.create_all()
    print("Database initialized!")

def to_float(number):
    try:
        return float(number.replace(",", "")) # remove ,
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

def build_filters_argument(args):
    """
    filters is an argument that is build joining different attributes for example
    # filters=MedianIncome-7236-200001_CostOfLivingIndex-14.3-1103.7
    """
    filters = []
    for attr in table_attributes:
        attr_min = args.get(f"min_{attr}", "")
        attr_max = args.get(f"max_{attr}", "")
        if attr_min or attr_max:
            name = "".join([p.capitalize() for p in attr.split("_")])
            filters.append(f"{name}-{attr_min}-{attr_max}")
    return "_".join(filters)

def get_zips_by_demographics():
    zips = []
    state = request.args.get("state_code")
    filters = build_filters_argument(request.args)
    url_arguments = urlencode({
        "filters": filters,
        "state": state,
        "mode": "demo",
    })
    full_url = f"https://zipwho.com/?{url_arguments}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(full_url)
        page.wait_for_selector("div#search_results_table", timeout=10000)
        table_content = page.inner_html("div#search_results_table")
        tree = html.fromstring(table_content)
        table_rows = tree.xpath("//tr")
        for row in table_rows:
            row_cells = row.xpath("./td")
            # if there are results the columns are more than 2
            if len(row_cells) > 2:
                link = row.xpath(".//a/text()")
                if link:
                    zips.append(link[0])
    return zips

@app.route('/zips_by_demographics', methods=['GET'])
def api_get_zips_by_demographics():
    zips = get_zips_by_demographics()
    if zips:
        return jsonify({"zips": [str(z) for z in zips]})
    else:
        return jsonify({"error": "no zips found"}), 404

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

    # as requirements only filters by demographics if state_code is given
    if request.args.get("state_code") is not None:
        zips = get_zips_by_demographics()
        query = query.filter(House.zip_code.in_(zips))

    # supports pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, max_per_page=500)

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

    response = house_to_dict(house)

    demographic = get_demographic(house.zip_code)
    if demographic:
        response["zip_info"] = demographic

    return jsonify(response)

def table_values(table_cells):
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
                parsed.append(to_float(number))
            i += 1
        return parsed

def table_parse(values):
    return dict(zip(table_attributes, values))

def get_result_table_cells(zip_code):
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
        return table_cells

def demographic_to_dict(demographic):
    return {
        "median_income": demographic.median_income,
        "cost_of_living_index": demographic.cost_of_living_index,
        "median_mortgage_to_income_ratio": demographic.median_mortgage_to_income_ratio,
        "owner_occupied_homes": demographic.owner_occupied_homes,
        "median_rooms_in_home": demographic.median_rooms_in_home,
        "college_degree": demographic.college_degree,
        "professional": demographic.professional,
        "population": demographic.population,
        "average_household_size": demographic.average_household_size,
        "median_age": demographic.median_age,
        "male_to_female_ratio": demographic.male_to_female_ratio,
        "married": demographic.married,
        "divorced": demographic.divorced,
        "white": demographic.white,
        "black": demographic.black,
        "asian": demographic.asian,
        "hispanic_ethnicity": demographic.hispanic_ethnicity,
        "zip_code": demographic.zip_code,
    }

def get_demographic(zip_code):
    demographic = Demographic.query.get(zip_code)
    if demographic:
        return demographic_to_dict(demographic)
    table_cells = get_result_table_cells(zip_code)
    values = table_values(table_cells)
    if values:
        parsed = table_parse(values)
        parsed["zip_code"] = zip_code
    else:
        # insert demographic without any values
        # so that next time it returns immediately
        parsed = {"zip_code": zip_code}
    with suppress(IntegrityError):
        new_demographic = Demographic(**parsed)
        db.session.add(new_demographic)
        db.session.commit()
    if values:
        return parsed

@app.route('/demographics/<string:zip_code>', methods=['GET'])
def api_get_demographic(zip_code):
    demographic = get_demographic(zip_code)
    if demographic:
        return jsonify({"result": demographic})
    else:
        return jsonify({"error": f"no data found for zip_code {zip_code}"}), 404

if __name__ == '__main__':
    app.run(debug=True)