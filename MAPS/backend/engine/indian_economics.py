"""
TrafficFlow-MAPS: Indian Smart City & MoRTH Economic Impact Calculator
Translates signal-aware proactive rerouting into verified fuel, carbon, and financial savings.
"""

from ..config import MAPS_CONFIG

class IndianEconomicsCalculator:
    def __init__(self):
        self.config = MAPS_CONFIG["ECONOMICS"]
        self.fuel_price = self.config["FUEL_PRICE_INR_PER_LITER"]
        self.time_value = self.config["COMMUTER_TIME_VALUE_INR_PER_HOUR"]
        self.idle_fuel_rate = self.config["IDLE_FUEL_LITERS_PER_HOUR"]
        self.co2_factor = self.config["CO2_KG_PER_LITER"]

    def calculate_reroute_savings(self, delay_saved_minutes: float, idle_saved_seconds: float):
        """
        Calculates trip-level and annualized savings for a proactive bypass diversion.
        """
        hours_saved = max(0.0, delay_saved_minutes / 60.0)
        idle_hours_saved = max(0.0, idle_saved_seconds / 3600.0)

        # Fuel Saved from avoiding queue idling
        fuel_saved_liters = round(idle_hours_saved * self.idle_fuel_rate, 3)
        fuel_savings_inr = round(fuel_saved_liters * self.fuel_price, 2)

        # Commuter Time Value Saved (MoRTH guideline: ₹150/hr for metropolitan transit)
        time_savings_inr = round(hours_saved * self.time_value, 2)

        # Total Net Savings for this trip
        total_trip_savings_inr = round(fuel_savings_inr + time_savings_inr, 2)

        # Carbon emissions abated
        co2_abated_kg = round(fuel_saved_liters * self.co2_factor, 3)

        # Corridor Annualized Impact (assuming 18,500 commuters/day on corridor)
        daily_commuters = self.config["AVERAGE_COMMUTERS_PER_DAY"]
        annual_fuel_saved_liters = round(fuel_saved_liters * daily_commuters * 300, 1)
        annual_co2_tonnes = round((co2_abated_kg * daily_commuters * 300) / 1000.0, 1)
        annual_savings_inr = round(total_trip_savings_inr * daily_commuters * 300, 2)
        annual_savings_lakhs = round(annual_savings_inr / 100000.0, 2)

        return {
            "delaySavedMinutes": round(delay_saved_minutes, 1),
            "idleTimeSavedSeconds": round(idle_saved_seconds, 1),
            "fuelSavedLiters": fuel_saved_liters,
            "fuelSavingsInr": fuel_savings_inr,
            "timeSavingsInr": time_savings_inr,
            "totalTripSavingsInr": total_trip_savings_inr,
            "co2AbatedKg": co2_abated_kg,
            "annualizedCorridor": {
                "annualFuelSavedLiters": annual_fuel_saved_liters,
                "annualCo2Tonnes": annual_co2_tonnes,
                "annualSavingsLakhs": annual_savings_lakhs
            }
        }
