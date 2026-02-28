import pandas as pd
import numpy as np
import scipy as sp

def climate_from_zip(zipcode: int):
    first = int(str(zipcode)[0])

    if first <= 2:
        return "northeast"
    elif first <= 5:
        return "central"
    elif first <= 8:
        return "mountain"
    else:
        return "west"

SOLAR_CF = {
    "northeast": 0.16,
    "central": 0.19,
    "mountain": 0.22,
    "west": 0.21,
}

WIND_CF = {
    "northeast": 0.18,
    "central": 0.25,
    "mountain": 0.30,
    "west": 0.24,
}

GEO_SAVINGS_FACTOR = {
    "northeast": 0.55,   # cold, big heating savings
    "central": 0.45,
    "mountain": 0.50,
    "west": 0.35,        # mild climates = smaller savings
}

def fast_npv(capex, annual_cash, years, r=0.05):
    pv_factor = (1 - (1 + r) ** -years) / r
    return -capex + annual_cash * pv_factor

class Dummy():
    """Solar energy solutions"""
    def __init__(self, zipcode: int, costperkWh: float, kWhperyear: float, costperBTU: float, BTUperyear: float, sqfeet: int, years: int):
        self.zipcode = zipcode
        self.costperkWh = costperkWh
        self.kWhperyear = kWhperyear
        self.costperBTU = costperBTU
        self.BTUperyear = BTUperyear
        self.sqfeet = sqfeet
        self.years = years
        self.name = "Dummy"
        
    def installCostSub(self):
        return 12.0

    def NPVsub(self):
        return 30.0
        
    def savingsOverTimeSub(self):
        return 1.0

class SolarFast:

    def __init__(
        self,
        zipcode: int,
        annual_kwh: float,
        electricity_rate: float,
        years: int,
    ):
        self.name = "Solar"
        self.zipcode = zipcode
        self.annual_kwh = annual_kwh
        self.rate = electricity_rate
        self.years = years

        self.region = climate_from_zip(zipcode)
        self.cf = SOLAR_CF[self.region]

        # assumptions
        self.offset_fraction = 0.80      # solar typically offsets more than wind
        self.capex_per_kw = 3000         # $/kW installed
        self.soft_cost = 2000            # permits, interconnection
        self.om_per_kw = 25              # $/kW-year
        self.federal_itc = 0.30          # 30% tax credit

    def system_size_kw(self):
        target_kwh = self.annual_kwh * self.offset_fraction
        return target_kwh / (8760 * self.cf)

    def annual_production(self):
        return self.system_size_kw() * 8760 * self.cf

    def installation_cost(self):
        gross = self.system_size_kw() * self.capex_per_kw + self.soft_cost
        return gross * (1 - self.federal_itc)

    def annual_savings(self):
        return self.annual_production() * self.rate

    def npv(self):
        capex = self.installation_cost()
        annual_om = self.system_size_kw() * self.om_per_kw
        net_cash = self.annual_savings() - annual_om

        return fast_npv(capex, net_cash, self.years)

    def payback_years(self):
        net_cash = self.annual_savings() - self.system_size_kw() * self.om_per_kw
        if net_cash <= 0:
            return 999
        return self.installation_cost() / net_cash

class WindFast:

    def __init__(self, zipcode, annual_kwh, electricity_rate, years):
        self.name = "Wind"
        self.zipcode = zipcode
        self.annual_kwh = annual_kwh
        self.rate = electricity_rate
        self.years = years

        self.region = climate_from_zip(zipcode)
        self.cf = WIND_CF[self.region]

        self.offset_fraction = 0.5
        self.capex_per_kw = 5000
        self.om_per_kw = 50

    def system_size_kw(self):
        target_kwh = self.annual_kwh * self.offset_fraction
        return target_kwh / (8760 * self.cf)

    def annual_savings(self):
        return self.annual_kwh * self.offset_fraction * self.rate

    def npv(self):
        kw = self.system_size_kw()
        self.capex = kw * self.capex_per_kw
        annual_om = kw * self.om_per_kw
        net_cash = self.annual_savings() - annual_om

        return fast_npv(self.capex, net_cash, self.years)

    def installation_cost(self):
        return self.capex

class GeoFast:

    def __init__(
        self,
        zipcode: int,
        annual_kwh: float,
        annual_btu: float,
        electricity_rate: float,
        gas_rate: float,
        years: int,
        sq_ft: float,
    ):
        self.name = "Geothermal"
        self.zipcode = zipcode
        self.annual_kwh = annual_kwh
        self.annual_btu = annual_btu
        self.electricity_rate = electricity_rate
        self.gas_rate = gas_rate
        self.years = years
        self.sq_ft = sq_ft

        self.climate = climate_from_zip(zipcode)
        self.savings_factor = GEO_SAVINGS_FACTOR[self.climate]

        # ---- Assumptions ----
        self.cost_per_ton = 4500          # installed cost per ton
        self.federal_itc = 0.30           # 30% geothermal ITC
        self.annual_om = 300              # yearly maintenance estimate

    def required_tonnage(self):
        # Rule of thumb: 1 ton per 600 sq ft
        return self.sq_ft / 600.0

    def installation_cost(self):
        gross = self.required_tonnage() * self.cost_per_ton
        return gross * (1 - self.federal_itc)

    def current_energy_cost(self):
        electric_cost = self.annual_kwh * self.electricity_rate
        gas_cost = self.annual_btu * self.gas_rate
        return electric_cost + gas_cost

    def annual_savings(self):
        return self.current_energy_cost() * self.savings_factor

    def annual_net_cash(self):
        return self.annual_savings() - self.annual_om

    def npv(self):
        capex = self.installation_cost()
        net_cash = self.annual_net_cash()
        return fast_npv(capex, net_cash, self.years)

    def payback_years(self):
        net_cash = self.annual_net_cash()
        if net_cash <= 0:
            return 999.0
        return self.installation_cost() / net_cash