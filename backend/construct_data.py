import pandas as pd
import Models

def build_dataset():
    energy_objects = []
    method = []
    installation_cost = []
    npv = []
    for energy_object in energy_objects:
        method.append(energy_object.name)
        installation_cost.append(energy_object.installCost())
        npv.append(energy_object.NPV())

    df = pd.DataFrame({
            "Method": method,
            "NPV": npv,
            "Installation Cost": installation_cost,
        })

    return df

def convert_dataset():
    #df = build_dataset()
    df = pd.DataFrame({
        "Method": ["Solar", "Wind", "Geothermal"],
        "NPV": [100, 300, 200]
        "Installation Cost": [100, 200, 300],
    })
    df_sorted = df.sort_values(by="NPV")
    df_json = df_sorted.to_json()
    return df_json
