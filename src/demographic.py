from contextlib import suppress
from sqlalchemy.exc import IntegrityError

from src.conf import db
from src.zipwho import get_result_table_cells, table_values, table_parse

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
    demographic = db.session.get(Demographic, zip_code)
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