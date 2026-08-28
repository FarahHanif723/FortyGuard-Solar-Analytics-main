"""
Solar panel output + heat-loss calculator.

Two effects, calculated separately so the demo can show them clearly:

1. IRRADIANCE -> how much sunlight is actually hitting the panel right now
   (GHI, W/m^2, from FortyGuard's env_params endpoint). Panels are rated
   at STC (Standard Test Conditions): 1000 W/m^2, 25 deg C cell temp.
   Actual output scales roughly linearly with GHI/1000.

2. HEAT -> panel efficiency drops as cell temperature rises above the
   25 deg C STC reference. Rate = temperature coefficient of power,
   typically -0.35% to -0.45% per degree C (we use -0.40%/C, adjustable
   per real panel spec sheets). Panel surface temp in direct sun runs
   ~20-25 deg C hotter than ambient air temp -- we use +22C.
"""

TEMP_COEFFICIENT_PERCENT_PER_C = 0.40
PANEL_TO_AMBIENT_OFFSET_C = 22.0
STC_REFERENCE_TEMP_C = 25.0
STC_IRRADIANCE_W_M2 = 1000.0


def calculate_solar_output(ambient_temp_c: float, ghi: float,
                            panel_capacity_kw: float,
                            electricity_rate_per_kwh: float,
                            sun_hours_per_day: float = 5.5) -> dict:
    """
    ambient_temp_c: from FortyGuard heatmap (°C)
    ghi: Global Horizontal Irradiance right now, W/m^2 (from env_params)
    panel_capacity_kw: rated (STC) capacity of the installation
    electricity_rate_per_kwh: local $/kWh
    sun_hours_per_day: used only for the daily/annual $ extrapolation
    """
    panel_temp_c = ambient_temp_c + PANEL_TO_AMBIENT_OFFSET_C
    degrees_above_ref = max(0.0, panel_temp_c - STC_REFERENCE_TEMP_C)
    efficiency_loss_percent = degrees_above_ref * TEMP_COEFFICIENT_PERCENT_PER_C

    irradiance_factor = min(1.0, max(0.0, (ghi or 0) / STC_IRRADIANCE_W_M2))

    # Output if only irradiance mattered (no heat penalty)
    output_no_heat_loss_kw = panel_capacity_kw * irradiance_factor
    # Actual output once heat is factored in
    actual_output_kw = output_no_heat_loss_kw * (1 - efficiency_loss_percent / 100.0)
    instantaneous_loss_kw = output_no_heat_loss_kw - actual_output_kw

    # Daily/annual extrapolation for a $-impact headline number
    ideal_kwh_per_day = panel_capacity_kw * sun_hours_per_day
    kwh_lost_per_day = ideal_kwh_per_day * (efficiency_loss_percent / 100.0)
    dollar_lost_per_day = kwh_lost_per_day * electricity_rate_per_kwh

    return {
        "ambient_temp_c": round(ambient_temp_c, 1),
        "panel_temp_c_estimate": round(panel_temp_c, 1),
        "ghi_w_m2": ghi,
        "efficiency_loss_percent": round(efficiency_loss_percent, 2),
        "output_no_heat_loss_kw": round(output_no_heat_loss_kw, 2),
        "actual_output_kw": round(actual_output_kw, 2),
        "instantaneous_loss_kw": round(instantaneous_loss_kw, 2),
        "kwh_lost_per_day": round(kwh_lost_per_day, 2),
        "kwh_lost_per_year": round(kwh_lost_per_day * 365, 1),
        "dollar_lost_per_day": round(dollar_lost_per_day, 2),
        "dollar_lost_per_year": round(dollar_lost_per_day * 365, 2),
        "risk_level": (
            "extreme" if efficiency_loss_percent > 15 else
            "high" if efficiency_loss_percent > 10 else
            "moderate" if efficiency_loss_percent > 5 else
            "low"
        )
    }


if __name__ == "__main__":
    result = calculate_solar_output(
        ambient_temp_c=42.5,
        ghi=850.0,
        panel_capacity_kw=6.0,
        electricity_rate_per_kwh=0.17
    )
    print(result)