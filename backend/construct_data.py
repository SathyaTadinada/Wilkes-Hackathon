import pandas as pd

def build_dataset():
    pass

def convert_dataset():
    #df = build_dataset()
    df = pd.DataFrame({
        "Method": ["Solar", "Wind", "Geothermal"],
        "Installation Cost": [100, 200, 300],
        "Cost Per Year": [200, 300, 400],
        "NPV": [100, 300, 200]
    })
    df_sorted = df.sort_values(by="age")
    df_json = df_sorted.to_json()
    return df_json
