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

class Model:
    """"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        self.zipcode = zipcode
        self.costperkWh = costperkWh
        self.kWhperyear = kWhperyear
        self.costperBTU = costperBTU
        self.BTUperyear = BTUperyear
        self.sqfeet = sqfeet
        self.years = years
        self.percentReplacements = np.array([0.1, 0.3, 1])
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
        
        if np.isnan(data):
            return self.totalAverageWeatherData[dataStr]
        else:
            return data
        
    def savings(self, Pa, electricity = True):
        """"""
        if electricity:
            return Pa * 8760 * self.costperkWh # 8760 hours in a year
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
    
class Dummy(Model):
    """Solar energy solutions"""
    
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        """"""
        super().__init__(zipcode, costperkWh, kWhperyear, costperBTU, BTUperyear, sqfeet, years)
        self.name = "Dummy"
        
    def installCost(self):
        return 12.0

    def NPV(self):
        return 30.0
        
    def savingsOverTime(self):
        return 1.0

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
        self.k_capex = 7850
        self.k_OM = 46
        self.Pa = self.kWhperyear/8760 * self.percentReplacements
        self.Pi = self.powerRated()
    
    def Area(self, P_rated):
        """returns area in meters for a given power rating
        https://docs.google.com/spreadsheets/d/1vxPFSOo5255XTnbqL5LU9BPplS1_HoSFddLY0MMfdlY/edit?usp=sharing"""
        return 12.1 + 4.27 * np.log(P_rated)
    
    def v_cutIn(self, P_rated):
        """https://docs.google.com/spreadsheets/d/1D1LJACNSzSjRHw3l2GSSJ7E_lHYuaRjZIAY-oMghpIU/edit?usp=sharing"""
        return 2.8 # m/s
    
    def v_rated(self, P_rated):
        """"""
        eta = 0.3 # efficiency
        rho = 1.225 # kg/m^3 https://en.wikipedia.org/wiki/Density_of_air sea level which is technically wrong for Utah
        return (2 * 1000 * P_rated/(eta * rho * self.Area(P_rated)))**(1/3) # m/s
    
    def powerCurve(v, P_rated, v_cutIn, v_rated):
        """ wind speed (v) in mph. 
        https://energyeducation.ca/encyclopedia/Wind_power#:~:text=Wind%20speed%20largely%20determines%20the,electrical%20power%20from%20the%20generator.
        """
        v_cutOut = np.inf
        
        a = P_rated/(v_rated - v_cutIn)**3
        
        if v < v_cutIn:
            return 0
        elif v_cutIn <= v < v_rated:
            return a * (v - v_cutIn)**3
        elif v_rated <= v < v_cutOut:
            return P_rated
        else:
            return 0
    
    def powerRated(self):
        """"""
        vms = 0.447 * self.getWeatherData("AWND") # average daily wind speed in m/s
        
        Pls = []
        
        for P_actual in self.Pa:
            func = lambda P_rated: Wind.powerCurve(vms, P_rated, self.v_cutIn(P_rated), self.v_rated(P_rated)) - P_actual
            a = 0.001 # kW
            b = 100000 # kW
            
            print("signs different?:", np.sign(func(a)) != np.sign(func(b)))
            if np.sign(func(a)) != np.sign(func(b)):
                P_r = sp.optimize.brentq(func, a, b)
            else:
                P_r = np.nan
                
            Pls.append(P_r)
            
        return np.array(Pls)
    
    def installCost(self):
        """https://solartechonline.com/blog/wind-turbine-cost-guide-2025/#:~:text=400W%20systems:%20$700%2D$850,only)%2C%20$80%2C000%2D$150%2C000%20installed"""
        return super().installCost(self.Pi, self.k_capex)
    
    def OMcost(self):
        """https://www.energy.gov/sites/default/files/2022-08/distributed_wind_market_report_2022.pdf?utm_source=chatgpt.com"""
        return super().OMcost(self.Pi, self.k_OM)
    
    def NPV(self):
        """"""
        return [super().NPV(self.Pa[i], self.Pi[i], self.k_capex, self.k_OM) for i in range(0, len(self.percentReplacements))]
        
    def savingsOverTime(self):
        return [super().savingsOverTime(self.Pa[i], self.Pi[i], self.k_capex, self.k_OM) for i in range(0, len(self.percentReplacements))]
    
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