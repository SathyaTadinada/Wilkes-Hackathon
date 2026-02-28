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
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int):
        """"""
        self.zipcode = zipcode
        self.costperkWh = costperkWh
        self.kWhperyear = kWhperyear
        self.costperBTU = costperBTU
        self.BTUperyear = BTUperyear
        self.sqfeet = sqfeet
        self.station = self.getStation()
        self.totalAverageWeatherData = weather_df.drop(columns = ["STATION", "NAME"]).mean()
        self.averageWeatherData = self.getAverageWeatherData()
        
    def getStation(self):
        """"""
        zipcodes = np.array(zip2station_df["Zip Code"])
        stations = np.array(zip2station_df["Station ID"])
        
        s = stations[zipcodes == self.zipcode]
        
        if len(s) < 1:
            return None
        else:
            return s[0]
        
    def getAverageWeatherData(self):
        """"""
        if self.station is None:
            return self.totalAverageWeatherData
        else:
            return weather_df.loc[weather_df["STATION"] == self.station].drop(columns = ["STATION", "NAME"]).mean()
        
    def getWeatherData(self, dataStr):
        """"""
        data = self.averageWeatherData[dataStr]
        
        print(np.isnan(data))
        if np.isnan(data):
            return self.totalAverageWeatherData[dataStr]
        else:
            return data
        
        
class Solar(Model):
    """Solar energy solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet)
        
class Wind(Model):
    """Wind energy solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet)
        
class Geo(Model):
    """Geothermal energy solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet)
        
    def cost(heat_pump_capacity, year):
        # in dollars
        cost_per_ton = 4000 # the paper assumes this
        return 
        
class DSM(Model):
    """Demand Side Management (DSM) solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet)