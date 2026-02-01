from zipwho import build_filters_argument, table_values

def test_build_filters_argument():
    args = {
        "min_median_income": 1000,
        "max_median_income": 2000,
        "min_cost_of_living_index": 1,
        "max_cost_of_living_index": 2,
        "others": 1,
    }
    filter = build_filters_argument(args)
    assert "MedianIncome-1000-2000_CostOfLivingIndex-1-2" == filter

def test_table_values():
    values = [
        "0", "1", "0",
        "0", "2", "0",
        "0", "3", "0",
        "0", "4", "0",
        "0", "5", "0",
        "0", "1", "0",
        "0", "2", "0",
        "0", "3", "0",
        "0", "4", "0",
        "0", "5", "0",
        "0", "1", "0",
        "0", "2", "0",
        "0", "3", "0",
        "0", "4", "0",
        "0", "5", "0",
        "0", "1", "0",
        "0", "2", "0",
    ]
    new_values = table_values(values)
    assert new_values == [1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1,2,]