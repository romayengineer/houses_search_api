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

4. install playwrignt and chromium

```sh
playwright install chromium
```

## Flask commands

### Create database

```sh
flask init-db
```

### download the CSV file

```sh
flask download-csv
```

it downloads the file into `realtor-data.csv`

### Import CSV file

the csv file has to be in the root of the app and have the name `realtor-data.csv`

```sh
flask import-csv
```

it takes 50 seconds to import +2 million rows

Import finished: 2224561 added
flask import-csv  36,37s user 12,67s system 98% cpu 49,705 total

### Scrapp zip codes

this loops over all the unique zip codes in the house table and scraps all the demographic data for those zip codes from zipwho.com

```sh
flask scrap-zip
```

## Run tests

```sh
pytest --cov=src


Name                 Stmts   Miss  Cover
----------------------------------------
src/__init__.py          0      0   100%
src/app.py             113     74    35%
src/browser.py           8      6    25%
src/conf.py             15      2    87%
src/demographic.py      41      1    98%
src/house.py            60      4    93%
src/zipwho.py           52      0   100%
----------------------------------------
TOTAL                  289     87    70%
```

## API endpoints

### List zip codes by demographics

```sh
curl "http://127.0.0.1:5000/zips_by_demographics?state_code=AK&min_median_income=10000"
```

### List Houses by properties

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

it also filters by demographic data and supports these arguments
- `min_median_income`
- `max_median_income`
- `min_cost_of_living_index`
- `max_cost_of_living_index`
- `min_median_mortgage_to_income_ratio`
- `max_median_mortgage_to_income_ratio`
- `min_owner_occupied_homes`
- `max_owner_occupied_homes`
- `min_median_rooms_in_home`
- `max_median_rooms_in_home`
- `min_college_degree`
- `max_college_degree`
- `min_professional`
- `max_professional`
- `min_population`
- `max_population`
- `min_average_household_size`
- `max_average_household_size`
- `min_median_age`
- `max_median_age`
- `min_male_to_female_ratio`
- `max_male_to_female_ratio`
- `min_married`
- `max_married`
- `min_divorced`
- `max_divorced`
- `min_white`
- `max_white`
- `min_black`
- `max_black`
- `min_asian`
- `max_asian`
- `min_hispanic_ethnicity`
- `max_hispanic_ethnicity`
- `min_zip_code`
- `max_zip_code`

### Get house by ID

```sh
curl "http://127.0.0.1:5000/properties/0000048afee0ea3f5d7232c5f06560830ccd2591ebc5d2c7f0c389c123d4c069"
```

```json
{
  "acre_lot": 55.8,
  "bath": "",
  "bed": "",
  "brokered_by": "25449.0",
  "city": "Jamestown",
  "house_size": 0.0,
  "id": "0000048afee0ea3f5d7232c5f06560830ccd2591ebc5d2c7f0c389c123d4c069",
  "prev_sold_date": "2022-01-24",
  "price": 79900.0,
  "price_per_acre": 1431.899641577061,
  "price_per_sq_ft": 0.0,
  "state": "Tennessee",
  "state_code": "TN",
  "status": "sold",
  "street": "1981876.0",
  "zip_code": "38556",
  "zip_info": {
    "asian": 0.0,
    "average_household_size": 2.4,
    "black": 0.1,
    "college_degree": 8.5,
    "cost_of_living_index": 55.1,
    "divorced": 13.8,
    "hispanic_ethnicity": 0.6,
    "male_to_female_ratio": 91.5,
    "married": 61.4,
    "median_age": 38.8,
    "median_income": 21831.0,
    "median_mortgage_to_income_ratio": 22.0,
    "median_rooms_in_home": 5.1,
    "owner_occupied_homes": 76.3,
    "population": 11974.0,
    "professional": 22.0,
    "white": 98.7,
    "zip_code": "38556"
  }
}
```

## Features

### Imdepotent import

the import is imdepotent because

1. Unique Identity: The id (the hash you generated) is a unique fingerprint of the row. SQLite will not allow two rows to have the same id.
2. Conflict Handling (OR IGNORE): If you run the script a second time, SQLite detects that the id already exists. Instead of crashing or creating a duplicate, the OR IGNORE command tells SQLite to silently skip that row.