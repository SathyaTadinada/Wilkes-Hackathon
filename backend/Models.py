# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 15:35:54 2026

@author: rohdo
"""

import pandas as pd
import numpy as np

weather_df = pd.read_csv("4244977.csv") # https://www.climate.gov/maps-data/dataset/past-weather-zip-code-data-table
zip2station_df = pd.read_csv("zipcodes.csv")
print(weather_df)

class House:
    """"""
    
    def __init__(self):
        """"""

class TaxCredit():
    """"""

class Model:
    """"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float):
        """"""
        self.zipcode = zipcode
        self.costperkWh = costperkWh
        self.kWhperyear = kWhperyear
        self.costperBTU = costperBTU
        self.BTUperyear = BTUperyear
        self.station = self.getStation()
        
    def getStation(self):
        """"""
        zipcodes = np.array(zip2station_df["Zip Code"])
        stations = np.array(zip2station_df["Station ID"])
        
        s = stations[zipcodes == self.zipcode]
        
        if len(s) < 1:
            return None
        else:
            return s[0]
        
    def averageData(self):
        """"""
        if self.station is None:
            return weather_df.drop(columns = ["STATION", "NAME"]).mean()
        else:
            return weather_df.loc[weather_df["STATION"] == self.station].drop(columns = ["STATION", "NAME"]).mean()
        
        
class Solar(Model):
    """Solar energy solutions"""
    
    def __init__(self, zipcode, budget):
        """"""
        super().__init__(zipcode, budget)
        
class Wind(Model):
    """Wind energy solutions"""
    
    def __init__(self, zipcode, budget):
        """"""
        super().__init__(zipcode, budget)
        
class Geo(Model):
    """Geothermal energy solutions"""
    
    def __init__(self, zipcode, budget):
        """"""
        super().__init__(zipcode, budget)
        
class DSM(Model):
    """Demand Side Management (DSM) solutions"""
    
    def __init__(self, zipcode, budget):
        """"""
        super().__init__(zipcode, budget)