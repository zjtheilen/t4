PROFILES = {
    "fantasy_overland": {
        "name": "Fantasy Overland (Eldmere)",
        "time_unit": "Days",
        "km_per_time_unit": 25.0,          # 25 km marched per day
        "resource_name": "Rations",
        "resource_burn_rate": 2.0,         # 2 rations consumed per day
        "hex_scale_km": 5.0,               # 1 hex = 5 km
    },
    "dcc_death_sport": {
        "name": "Syndicate Death-Sport (DCC)",
        "time_unit": "Hours",
        "km_per_time_unit": 5.0,           # 5 km crawled per hour in hazardous sectors
        "resource_name": "Battery Charge (%)",
        "resource_burn_rate": 4.5,         # 4.5% battery burned per hour/km effort
        "hex_scale_km": 1.0,               # 1 hex = 1 km zone sector
    },
    "backrooms_survival": {
        "name": "Surreal Survival (The Backrooms)",
        "time_unit": "Entity Cycles",
        "km_per_time_unit": 2.0,           # Non-euclidean distortion slowdown
        "resource_name": "Sanity / Fluid (mL)",
        "resource_burn_rate": 15.0,        # High mental/physical toll per cycle
        "hex_scale_km": 1.0,
    }
}
