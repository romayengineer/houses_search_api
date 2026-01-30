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

## Features

### Imdepotent import

the import is imdepotent because

1. Unique Identity: The id (the hash you generated) is a unique fingerprint of the row. SQLite will not allow two rows to have the same id.
2. Conflict Handling (OR IGNORE): If you run the script a second time, SQLite detects that the id already exists. Instead of crashing or creating a duplicate, the OR IGNORE command tells SQLite to silently skip that row.