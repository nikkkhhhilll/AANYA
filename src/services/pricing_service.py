"""
Pricing Configuration Service for GIM Campus Mobility.
Allows Transport Admin to modify pricing dynamically, persisting values in system_settings database table.
Falls back to config default constants when database is uninitialized.
"""
import json
import streamlit as st
from typing import Dict, Any, Optional
from src.db import DBService

# Default values from config/defaults as hard fallback
DEFAULT_CAB_FARE_RULES = {
    "Hatchback": {"base_fare": 60.0, "rate_per_km": 20.0},
    "Sedan": {"base_fare": 80.0, "rate_per_km": 22.0},
    "SUV": {"base_fare": 100.0, "rate_per_km": 25.0}
}

DEFAULT_SELF_DRIVE_HOURLY_RATES = {
    "SUV": 105.0,
    "Sedan": 70.0,
    "Hatchback": 70.0,
    "Bike": 55.0,
    "Scooty": 40.0
}


class PricingService:
    """Service to get/set dynamic cab and self-drive pricing rules."""

    @staticmethod
    def get_pricing_config() -> Dict[str, Any]:
        """Fetch full pricing configuration from database settings table, or return defaults."""
        try:
            # Query settings
            records = DBService.query("system_settings", filters={"key": "pricing_config"}, limit=1)
            if records:
                val = records[0].get("value")
                if isinstance(val, str):
                    return json.loads(val)
                elif isinstance(val, dict):
                    return val
        except Exception:
            pass

        # Fallback to local memory cache if set
        if "pricing_config_cache" in st.session_state:
            return st.session_state["pricing_config_cache"]

        # Default configuration payload
        config = {
            "cab_fare_rules": DEFAULT_CAB_FARE_RULES,
            "self_drive_hourly_rates": DEFAULT_SELF_DRIVE_HOURLY_RATES
        }
        st.session_state["pricing_config_cache"] = config
        return config

    @staticmethod
    def get_cab_fare_rules() -> Dict[str, Dict[str, float]]:
        """Fetch cab base fare and rate per km rules."""
        config = PricingService.get_pricing_config()
        return config.get("cab_fare_rules", DEFAULT_CAB_FARE_RULES)

    @staticmethod
    def get_self_drive_hourly_rates() -> Dict[str, float]:
        """Fetch self-drive hourly rental rates."""
        config = PricingService.get_pricing_config()
        return config.get("self_drive_hourly_rates", DEFAULT_SELF_DRIVE_HOURLY_RATES)

    @staticmethod
    def update_pricing(cab_rules: Dict[str, Dict[str, float]], self_drive_rates: Dict[str, float]) -> bool:
        """Update global pricing configs in the database."""
        config = {
            "cab_fare_rules": cab_rules,
            "self_drive_hourly_rates": self_drive_rates
        }
        # Update session state cache
        st.session_state["pricing_config_cache"] = config
        
        # Save to database
        try:
            # Check if key exists
            records = DBService.query("system_settings", filters={"key": "pricing_config"}, limit=1)
            if records:
                # Update
                DBService.update("system_settings", "pricing_config", {"value": config})
            else:
                # Insert
                DBService.insert("system_settings", {"key": "pricing_config", "value": config})
            return True
        except Exception:
            # Fallback update in SQLite directly
            try:
                engine = DBService.get_engine()
                cur = engine.conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                    ("pricing_config", json.dumps(config))
                )
                engine.conn.commit()
                return True
            except Exception:
                return False
