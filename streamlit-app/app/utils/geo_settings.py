"""
Geographic settings and configuration for Speed Local energy flow mapping
"""
import pandas as pd

# Regional coordinates for special locations
SPECIAL_REGIONS = {
    "Global Market": (55.511515, 15.987998),
    "BORNHOLM": (55.1, 14.9),
    "DKISL1": (55.979076, 7.096848),
    "DKISL2": (56.068326, 6.603515), 
    "DKISL3": (56.193403, 6.350176),
    "DEISL": (55.136747, 6.205615),
    "DKISLBH": (55.136895, 14.902472)
}

# Default map center (Bornholm region)
MAP_CENTER = [55.12, 14.92]
DEFAULT_ZOOM = 8

# Map styling
MAP_TILE = "CartoDB positron"
MAX_LINE_WIDTH = 15
MIN_LINE_WIDTH = 2