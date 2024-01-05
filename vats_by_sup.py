# get data from this month
# Month - Year
# Sup - num of vats

import pandas as pd

def vats_by_sup():
    data = pd.read_csv("/home/ilyas/Desktop/Projects/fred/fred/vats.csv")

    first_col = "Who monitored & conducted the vigilance test? (First)"
    last_col = "Who monitored & conducted the vigilance test? (Last)"

    original_date_col = "Date of Vigilance Test Conducted"

    data['date'] = pd.to_datetime(data[original_date_col], format='%b %d, %Y')
    data['month'] = data['date'].dt.month
    data['year'] = data['date'].dt.year

    data['first_last'] = data[first_col].fillna('') + " " + data[last_col].fillna('')
    
    #current month
    current_month = 11
    current_year = 2023
    month_data = data[(data["year"] == current_year) & (data["month"] == current_month)]

    #grouping by name - count
    month_data['count'] = month_data.groupby('first_last')['first_last'].transform('count')

    for index, row in month_data[[first_col, last_col, "count"]].drop_duplicates().iterrows():
        print(f"Supervisor {row[first_col]} {row[last_col]}: {row['count']}")


print(vats_by_sup())

