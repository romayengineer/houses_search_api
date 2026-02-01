
from flask import request
from lxml import html
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright
from conf import to_float

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