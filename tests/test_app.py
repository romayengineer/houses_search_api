from src.house import house_attrs

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

def house_fill_with_none(house):
    new_house = {}
    for attr in house_attrs:
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
            house_fill_with_none({
                'id': 'hash1',
                'bed': 3,
                'price': 500000.0,
                'status': 'for_sale',
            }),
            house_fill_with_none({
                'id': 'hash2',
                'bed': 2,
                'price': 250000.0,
                'status': 'for_sale',
            }),
        ],
    }