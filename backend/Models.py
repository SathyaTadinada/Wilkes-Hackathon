# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 15:35:54 2026

@author: rohdo
"""

import pandas as pd
import numpy as np
import scipy as sp

weather_df = pd.read_csv("4244977.csv") # https://www.climate.gov/maps-data/dataset/past-weather-zip-code-data-table
zip2station_df = pd.read_csv("zipcodes.csv")

class House:
    """"""
    
    def __init__(self):
        """"""

class TaxCredit():
    """"""

class Model:
    """"""
    
    percentReplacements = np.array([0.1, 0.3, 1])
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        self.zipcode = zipcode
        self.costperkWh = costperkWh
        self.kWhperyear = kWhperyear
        self.costperBTU = costperBTU
        self.BTUperyear = BTUperyear
        self.sqfeet = sqfeet
        self.years
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
        
    def savings(self, Pa, electricity = True):
        """"""
        if electricity:
            return Pa * self.costperkWh
        else:
            return Pa * self.costperBTU
    
    def installCost(self, Pi, k_capex):
        """"""
        return k_capex * Pi
    
    def OMcost(self, Pi, k_OM):
        """"""
        return k_OM * Pi
    
    def NPV(self, Pa, Pi, k_capex, k_OM, r = 0.024, electricity = True):
        """"""
        capex = self.installCost(Pi, k_capex)
        
        sav = self.savings(Pa, electricity = electricity)
            
        OM = self.OMcost(Pi, k_OM) # operating and management costs
        
        return -capex + sum((sav - OM)/(1 + r)**t for t in range(0, self.years))
    
    def savingsOverTime(self, Pa, Pi, k_OM, electricity = True):
        """"""
        sav = self.savings(Pa, electricity = electricity)
        OM = self.OMcost(Pi, k_OM) # operating and management costs
        
        return sum(sav - OM for t in range(0, self.years))
        
    
class Solar(Model):
    """Solar energy solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet, years)
        
class Wind(Model):
    """Wind energy solutions"""
    
    # cost vs kW curves
    # https://solartechonline.com/blog/wind-turbine-cost-guide-2025/#:~:text=400W%20systems:%20$700%2D$850,only)%2C%20$80%2C000%2D$150%2C000%20installed
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet, years)
    
    def installCost(kW):
        """https://solartechonline.com/blog/wind-turbine-cost-guide-2025/#:~:text=400W%20systems:%20$700%2D$850,only)%2C%20$80%2C000%2D$150%2C000%20installed"""
        return 7850 * kW
    
    def v_cutIN(self, P_rated):
        """"""
        return 1
    
    def v_rated(self, P_rated):
        """"""
        return 1
    
    def power(v, P_rated, v_cutIn, v_rated, v_cutOut = np.inf):
        """ wind speed (v) in mph. 
        https://energyeducation.ca/encyclopedia/Wind_power#:~:text=Wind%20speed%20largely%20determines%20the,electrical%20power%20from%20the%20generator.
        """
        a = P_rated/(v_rated - v_cutIn)**3
        
        if v < v_cutIn:
            return 0
        elif v_cutIn <= v < v_rated:
            return a * (v - v_cutIn)**3
        elif v_rated <= v < v_cutOut:
            return 1
        else:
            return 0
        
    
        
class Geo(Model):
    """Geothermal energy solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet, years)
        
    def cost(heat_pump_capacity, year):
        # in dollars
        cost_per_ton = 4000 # the paper assumes this
        return 
        
class DSM(Model):
    """Demand Side Management (DSM) solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet, years)