from src.house import house_attrs
from src.demographic import demographic_attrs

zips = ["111", "222", "333", "444"]

zips_table_content = [
    (
        "  <tr>"
        "    <td>n</td>"
        "    <td><a>%s<br>state name</a></td>"
        "    <td>value</td>"
        "  </tr>"
    ) % i
    for i in zips
]

zips_table = (
    "<table>"
    "%s"
    "</table>"
) % zips_table_content

def fill_with_none(house, attrs):
    new_house = house.copy()
    for attr in attrs:
        new_house[attr] = house.get(attr)
    return new_house

def test_api_get_zips_by_demographics(client, mocker):
    goto_and_select = mocker.patch("src.zipwho.goto_and_select")
    goto_and_select.return_value = zips_table
    params = {
        'state_code': 'AK',
        'min_median_income': 10000
    }
    response = client.get("/zips_by_demographics", query_string=params)
    assert response.status_code == 200
    assert response.json == {'zips': zips}

def test_api_get_house_by_property(client, mocker):
    goto_and_select = mocker.patch("src.zipwho.goto_and_select")
    goto_and_select.return_value = ""
    params = {
        "status": "for_sale",
        "min_price": "200000",
        "max_price": "600000",
    }
    response = client.get("/properties", query_string=params)
    assert response.status_code == 200
    assert response.json == {
        'current_page': 1,
        'pages': 1,
        'per_page': 20,
        'total': 2,
        'results': [
            fill_with_none({
                'id': 'hash2',
                'bed': 2,
                'price': 200000.0,
                'status': 'for_sale',
                'zip_code': '222',
            }, house_attrs),
            fill_with_none({
                'id': 'hash3',
                'bed': 3,
                'price': 300000.0,
                'status': 'for_sale',
                'zip_code': '333',
            }, house_attrs),
        ],
    }

def test_api_get_property_by_id(client, mocker):
    goto_and_select = mocker.patch("src.zipwho.goto_and_select")
    goto_and_select.return_value = ""
    response = client.get("/properties/hash1")
    assert response.status_code == 200
    assert response.json == fill_with_none({
        'bed': 1,
        'id': 'hash1',
        'price': 100000.0,
        'status': 'for_sale',
        'zip_code': '111',
        'zip_info': fill_with_none({
            'median_income': 111.0,
            'zip_code': '111'
        }, demographic_attrs)
    }, house_attrs)

def test_api_get_demographic(client, mocker):
    goto_and_select = mocker.patch("src.zipwho.goto_and_select")
    goto_and_select.return_value = ""
    response = client.get("/demographics/111")
    assert response.status_code == 200
    assert response.json == {
        "result": fill_with_none({
            'median_income': 111.0,
            'zip_code': '111'
        }, demographic_attrs),
    }