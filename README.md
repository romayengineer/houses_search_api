# Houses Search API

## How to install

1. create virtual environment

```sh
python -m venv venv
```

2. activate environment

```sh
source venv/bin/activate
```

3. install dependencies

```sh
pip install -r requirements
```

4. install playwrignt and cromium

```sh
playwright install chromium
```

## Create database

```sh
flask init-db
```

## download the CSV file

```sh
flask download-csv
```

it downloads the file into `realtor-data.csv`

## Import CSV file

the csv file has to be in the root of the app and have the name `realtor-data.csv`

```sh
flask import-csv
```

it takes 50 seconds to import +2 million rows

Import finished: 2224561 added
flask import-csv  36,37s user 12,67s system 98% cpu 49,705 total

## API endpoints

### Search house by properties

for example

```sh
curl "http://127.0.0.1:5000/properties?min_price=500000&max_price=800000&min_bed=3&status=for_sale&state=California"
```

it supports the following arguments for filtering
- `status` required - possible values: `for_sale | sold | ready_to_build`
- `min_price`
- `max_price`
- `min_bed`
- `max_bed`
- `min_bath`
- `max_bath`
- `min_acre_lot`
- `max_acre_lot`
- `min_price_per_acre`
- `max_price_per_acre`
- `min_house_size`
- `max_house_size`
- `min_price_per_sqft`
- `max_price_per_sqft`
- `city`
- `state`
- `state_code` - required for demographics search
- `zip_code`

## Features

### Imdepotent import

the import is imdepotent because

1. Unique Identity: The id (the hash you generated) is a unique fingerprint of the row. SQLite will not allow two rows to have the same id.
2. Conflict Handling (OR IGNORE): If you run the script a second time, SQLite detects that the id already exists. Instead of crashing or creating a duplicate, the OR IGNORE command tells SQLite to silently skip that row.