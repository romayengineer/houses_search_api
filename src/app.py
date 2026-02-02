import os
import csv
import hashlib
import sqlite3
import requests
from flask import jsonify, request

from src.conf import app, basedir, db_path, db, state_map, to_float
from src.house import House, get_house_by_property, house_to_dict
from src.demographic import get_demographic
from src.zipwho import get_zips_by_demographics

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

@app.cli.command("init-db")
def command_init_db():
    """Clear existing data and create new tables."""
    db.create_all()
    print("Database initialized!")

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
    dest_path = os.path.join(basedir, "realtor-data.csv")
    print(f"Downloading {url}...")
    # stream=True allows us to download the file in pieces
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    print(f"Download complete: {dest_path}")

@app.route('/zips_by_demographics', methods=['GET'])
def api_get_zips_by_demographics():
    zips = get_zips_by_demographics(request.args)
    if zips:
        return jsonify({"zips": [str(z) for z in zips]})
    else:
        return jsonify({"error": "no zips found"}), 404

@app.route('/properties', methods=['GET'])
def api_get_house_by_property():
    pagination = get_house_by_property(request.args)
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
    house = db.session.get(House, house_id)

    if not house:
        return jsonify({"error": "Property not found"}), 404

    response = house_to_dict(house)

    demographic = get_demographic(house.zip_code)
    if demographic:
        response["zip_info"] = demographic

    return jsonify(response)

@app.route('/demographics/<string:zip_code>', methods=['GET'])
def api_get_demographic(zip_code):
    demographic = get_demographic(zip_code)
    if demographic and demographic.get("median_income") is not None:
        return jsonify({"result": demographic})
    else:
        return jsonify({"error": f"no data found for zip_code {zip_code}"}), 404

if __name__ == '__main__':
    app.run(debug=True)