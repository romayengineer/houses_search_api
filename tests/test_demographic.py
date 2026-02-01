from src.demographic import get_demographic

def test_get_demographics_1(app):
    demographic = get_demographic(123)
    assert demographic == {
        'median_income': 123.0,
        'cost_of_living_index': None,
        'median_mortgage_to_income_ratio': None,
        'owner_occupied_homes': None,
        'median_rooms_in_home': None,
        'college_degree': None,
        'professional': None,
        'population': None,
        'average_household_size': None,
        'median_age': None,
        'male_to_female_ratio': None,
        'married': None,
        'divorced': None,
        'white': None,
        'black': None,
        'asian': None,
        'hispanic_ethnicity': None,
        'zip_code': '123'
    }

row_content = [
    (
        "  <tr>"
        "    <td>%s</td>"
        "    <td>%s</td>"
        "    <td>%s</td>"
        "  </tr>"
    ) % (3*i+1, 3*i+2, 3*i+3)
    for i in range(17)
]

table_content = (
    "<table>"
    "%s"
    "</table>"
) % row_content

def test_get_demographics_2(app, mocker):
    goto_and_select = mocker.patch("src.zipwho.goto_and_select")
    goto_and_select.return_value = table_content
    demographic = get_demographic(555)
    assert demographic == {
        'median_income': 2.0,
        'cost_of_living_index': 5.0,
        'median_mortgage_to_income_ratio': 8.0,
        'owner_occupied_homes': 11.0,
        'median_rooms_in_home': 14.0,
        'college_degree': 17.0,
        'professional': 20.0,
        'population': 23.0,
        'average_household_size': 26.0,
        'median_age': 29.0,
        'male_to_female_ratio': 32.0,
        'married': 35.0,
        'divorced': 38.0,
        'white': 41.0,
        'black': 44.0,
        'asian': 47.0,
        'hispanic_ethnicity': 50.0,
        'zip_code': 555
    }