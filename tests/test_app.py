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

def test_zips_by_demographics(client, mocker):
    goto_and_select = mocker.patch("src.zipwho.goto_and_select")
    goto_and_select.return_value = zips_table
    params = {
        'state_code': 'AK',
        'min_median_income': 10000
    }
    response = client.get('/zips_by_demographics', query_string=params)
    assert response.status_code == 200
    assert response.json == {'zips': zips}