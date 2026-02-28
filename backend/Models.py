from __future__ import annotations

from typing import Any, Dict, List


def climate_from_zip(zipcode: int) -> str:
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
    "northeast": 0.55,
    "central": 0.45,
    "mountain": 0.50,
    "west": 0.35,
}


# -----------------------------
# Energy Efficiency assumptions
# -----------------------------

# Fraction of total annual energy spend saved by each measure (made-up but plausible)
EE_SAVINGS_FRACTION = {
    "insulation": {
        "northeast": 0.12,
        "central": 0.10,
        "mountain": 0.11,
        "west": 0.07,
    },
    "air_sealing": {
        "northeast": 0.08,
        "central": 0.07,
        "mountain": 0.07,
        "west": 0.05,
    },
    "smart_thermostat": {
        "northeast": 0.06,
        "central": 0.06,
        "mountain": 0.06,
        "west": 0.05,
    },
    "led_lighting": {
        "northeast": 0.03,
        "central": 0.03,
        "mountain": 0.03,
        "west": 0.03,
    },
    "heat_pump_water_heater": {
        "northeast": 0.07,
        "central": 0.06,
        "mountain": 0.06,
        "west": 0.05,
    },
    "duct_sealing": {
        "northeast": 0.06,
        "central": 0.06,
        "mountain": 0.06,
        "west": 0.04,
    },
    "windows": {
        "northeast": 0.05,
        "central": 0.04,
        "mountain": 0.04,
        "west": 0.03,
    },
}

EE_INSTALL_COST = {
    "insulation": 2500,
    "air_sealing": 800,
    "smart_thermostat": 250,
    "led_lighting": 400,
    "heat_pump_water_heater": 1800,
    "duct_sealing": 1200,
    "windows": 4000,
}

# Utility rebates (keep hackathon-simple; made-up/UT-ish)
EE_UTILITY_REBATE = {
    "insulation": 600,
    "air_sealing": 150,
    "smart_thermostat": 75,
    "led_lighting": 0,
    "heat_pump_water_heater": 300,
    "duct_sealing": 250,
    "windows": 300,
}

# Federal credit fraction + caps (simplified)
EE_FEDERAL_CREDIT_FRACTION = {
    "insulation": 0.30,
    "air_sealing": 0.30,
    "smart_thermostat": 0.00,
    "led_lighting": 0.00,
    "heat_pump_water_heater": 0.30,
    "duct_sealing": 0.00,
    "windows": 0.30,
}
EE_FEDERAL_CREDIT_CAP = {
    "insulation": 1200,
    "air_sealing": 1200,
    "smart_thermostat": 0,
    "led_lighting": 0,
    "heat_pump_water_heater": 2000,
    "duct_sealing": 0,
    "windows": 600,
}


BTU_PER_KWH = 3412.0


def fast_npv(capex: float, annual_cash: float, years: float, r: float = 0.05) -> float:
    pv_factor = (1 - (1 + r) ** -years) / r
    return -capex + annual_cash * pv_factor


def total_kwh_equivalent(annual_kwh: float, annual_btu: float) -> float:
    return float(annual_kwh) + (float(annual_btu) / BTU_PER_KWH)


def avg_cost_per_kwh_equivalent(
    annual_kwh: float,
    annual_btu: float,
    electricity_rate: float,
    gas_rate: float,
) -> float:
    total_cost = (float(annual_kwh) * float(electricity_rate)) + (float(annual_btu) * float(gas_rate))
    kwh_eq = total_kwh_equivalent(annual_kwh, annual_btu)
    return (total_cost / kwh_eq) if kwh_eq > 0 else float(electricity_rate)


class SolarFast:
    def __init__(self, zipcode: int, annual_kwh: float, electricity_rate: float, years: int):
        self.name = "Solar"
        self.zipcode = zipcode
        self.annual_kwh = float(annual_kwh)
        self.rate = float(electricity_rate)
        self.years = int(years)

        self.region = climate_from_zip(zipcode)
        self.cf = SOLAR_CF[self.region]

        self.offset_fraction = 0.80
        self.capex_per_kw = 3000
        self.soft_cost = 2000
        self.om_per_kw = 25
        self.federal_itc = 0.30

    def system_size_kw(self) -> float:
        target_kwh = self.annual_kwh * self.offset_fraction
        return target_kwh / (8760 * self.cf)

    def annual_production(self) -> float:
        return self.system_size_kw() * 8760 * self.cf

    def installation_cost(self) -> float:
        gross = self.system_size_kw() * self.capex_per_kw + self.soft_cost
        return gross * (1 - self.federal_itc)

    def annual_savings(self) -> float:
        return self.annual_production() * self.rate

    def annual_energy_savings_kwh_eq(self) -> float:
        # kWh produced ~ kWh offset
        return self.annual_production()

    def npv(self) -> float:
        capex = self.installation_cost()
        annual_om = self.system_size_kw() * self.om_per_kw
        net_cash = self.annual_savings() - annual_om
        return fast_npv(capex, net_cash, self.years)

    def payback_years(self) -> float:
        net_cash = self.annual_savings() - self.system_size_kw() * self.om_per_kw
        if net_cash <= 0:
            return 999.0
        return self.installation_cost() / net_cash


class WindFast:
    def __init__(self, zipcode: int, annual_kwh: float, electricity_rate: float, years: int):
        self.name = "Wind"
        self.zipcode = zipcode
        self.annual_kwh = float(annual_kwh)
        self.rate = float(electricity_rate)
        self.years = int(years)

        self.region = climate_from_zip(zipcode)
        self.cf = WIND_CF[self.region]

        self.offset_fraction = 0.50
        self.capex_per_kw = 5000
        self.om_per_kw = 50

        self.capex = 0.0

    def system_size_kw(self) -> float:
        target_kwh = self.annual_kwh * self.offset_fraction
        return target_kwh / (8760 * self.cf)

    def annual_savings(self) -> float:
        return self.annual_kwh * self.offset_fraction * self.rate

    def annual_energy_savings_kwh_eq(self) -> float:
        # simple: assume offsets offset_fraction of yearly usage
        return self.annual_kwh * self.offset_fraction

    def npv(self) -> float:
        kw = self.system_size_kw()
        self.capex = kw * self.capex_per_kw
        annual_om = kw * self.om_per_kw
        net_cash = self.annual_savings() - annual_om
        return fast_npv(self.capex, net_cash, self.years)

    def installation_cost(self) -> float:
        if self.capex <= 0:
            self.capex = self.system_size_kw() * self.capex_per_kw
        return self.capex

    def payback_years(self) -> float:
        net_cash = self.annual_savings() - self.system_size_kw() * self.om_per_kw
        if net_cash <= 0:
            return 999.0
        return self.installation_cost() / net_cash


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
        self.annual_kwh = float(annual_kwh)
        self.annual_btu = float(annual_btu)
        self.electricity_rate = float(electricity_rate)
        self.gas_rate = float(gas_rate)
        self.years = int(years)
        self.sq_ft = float(sq_ft)

        self.climate = climate_from_zip(zipcode)
        self.savings_factor = GEO_SAVINGS_FACTOR[self.climate]

        self.cost_per_ton = 4500
        self.federal_itc = 0.30
        self.annual_om = 300.0

    def required_tonnage(self) -> float:
        return self.sq_ft / 600.0

    def installation_cost(self) -> float:
        gross = self.required_tonnage() * self.cost_per_ton
        return gross * (1 - self.federal_itc)

    def current_energy_cost(self) -> float:
        electric_cost = self.annual_kwh * self.electricity_rate
        gas_cost = self.annual_btu * self.gas_rate
        return electric_cost + gas_cost

    def annual_savings(self) -> float:
        return self.current_energy_cost() * self.savings_factor

    def annual_energy_savings_kwh_eq(self) -> float:
        # convert $ saved -> kWh-equivalent saved using blended $/kWh-eq
        blended = avg_cost_per_kwh_equivalent(
            self.annual_kwh, self.annual_btu, self.electricity_rate, self.gas_rate
        )
        return (self.annual_savings() / blended) if blended > 0 else 0.0

    def annual_net_cash(self) -> float:
        return self.annual_savings() - self.annual_om

    def npv(self) -> float:
        return fast_npv(self.installation_cost(), self.annual_net_cash(), self.years)

    def payback_years(self) -> float:
        net_cash = self.annual_net_cash()
        if net_cash <= 0:
            return 999.0
        return self.installation_cost() / net_cash


class EnergyEfficiencyFast:
    ALL_MEASURES = list(EE_INSTALL_COST.keys())

    def __init__(
        self,
        zipcode: int,
        annual_kwh: float,
        electricity_rate: float,
        annual_btu: float,
        gas_rate: float,
        years: int,
        measures: List[str] | None = None,
    ):
        self.name = "Internal Home Solutions"
        self.zipcode = zipcode
        self.annual_kwh = float(annual_kwh)
        self.electricity_rate = float(electricity_rate)
        self.annual_btu = float(annual_btu)
        self.gas_rate = float(gas_rate)
        self.years = int(years)
        self.measures = measures if measures is not None else self.ALL_MEASURES

        self.climate = climate_from_zip(zipcode)
        self.annual_om = 50.0

    def gross_install_cost(self, measure: str) -> float:
        return float(EE_INSTALL_COST[measure])

    def utility_rebate(self, measure: str) -> float:
        return float(EE_UTILITY_REBATE[measure])

    def federal_credit(self, measure: str) -> float:
        gross = float(EE_INSTALL_COST[measure])
        credit = gross * float(EE_FEDERAL_CREDIT_FRACTION[measure])
        cap = float(EE_FEDERAL_CREDIT_CAP[measure])
        return min(credit, cap) if cap > 0 else credit

    def net_install_cost(self, measure: str) -> float:
        return self.gross_install_cost(measure) - self.utility_rebate(measure) - self.federal_credit(measure)

    def installation_cost(self) -> float:
        return sum(self.net_install_cost(m) for m in self.measures)

    def annual_savings_raw(self) -> float:
        total_annual_cost = (self.annual_kwh * self.electricity_rate) + (self.annual_btu * self.gas_rate)
        return sum(float(EE_SAVINGS_FRACTION[m][self.climate]) * total_annual_cost for m in self.measures)

    def annual_savings(self) -> float:
        raw = self.annual_savings_raw()
        overlap_discount = 0.80 if len(self.measures) > 1 else 1.0
        return raw * overlap_discount

    def annual_energy_savings_kwh_eq(self) -> float:
        blended = avg_cost_per_kwh_equivalent(
            self.annual_kwh, self.annual_btu, self.electricity_rate, self.gas_rate
        )
        return (self.annual_savings() / blended) if blended > 0 else 0.0

    def annual_net_cash(self) -> float:
        return self.annual_savings() - self.annual_om

    def npv(self) -> float:
        return fast_npv(self.installation_cost(), self.annual_net_cash(), self.years)

    def payback_years(self) -> float:
        net_cash = self.annual_net_cash()
        if net_cash <= 0:
            return 999.0
        return self.installation_cost() / net_cash