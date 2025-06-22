"""Support for Utility Water Meter sensors."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    StatisticData,
    StatisticMetaData,
    async_add_external_statistics,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
from .scraper import UtilityDataScraper

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Utility Water Meter sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Create statistics-based sensor
    entities = [
        UtilityWaterStatisticsSensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class UtilityWaterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the utility meter and importing statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.username = username
        self.password = password
        self.scraper = UtilityDataScraper()
        self._hass = hass
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library and import statistics."""
        try:
            data = await self.hass.async_add_executor_job(
                self.scraper.get_latest_data, self.username, self.password
            )
            if not data:
                raise UpdateFailed("Failed to fetch data from utility meter")
            
            # Import statistics for Energy dashboard
            await self._async_import_statistics(data)
            
            return data
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception

    async def _async_import_statistics(self, data: dict[str, Any]) -> None:
        """Import hourly usage statistics into Home Assistant recorder."""
        if not data.get("all_records"):
            _LOGGER.warning("No usage records to import as statistics")
            return

        # Create statistics metadata
        statistic_id = f"{DOMAIN}:water_usage_hourly"
        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name="Water Usage (Hourly)",
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_of_measurement=UnitOfVolume.GALLONS,
        )

        # Convert usage records to statistics
        statistics = []
        cumulative_sum = 0
        
        for record in data["all_records"]:
            try:
                # Parse the datetime string from the utility data
                # Format: "Thu, Jun 19, 2025 4:00 AM - 5:00 AM"
                datetime_str = record["datetime"]
                # Extract just the start time part
                start_time_str = datetime_str.split(" - ")[0]
                
                # Parse the datetime
                record_time = datetime.strptime(start_time_str, "%a, %b %d, %Y %I:%M %p")
                record_time = dt_util.as_utc(record_time)
                
                # Add this hour's usage to cumulative total
                cumulative_sum += record["usage_gallons"]
                
                # Create statistic data point
                stat_data = StatisticData(
                    start=record_time,
                    sum=cumulative_sum,  # Cumulative sum for Energy dashboard
                    state=record["usage_gallons"],  # Individual hourly usage
                )
                statistics.append(stat_data)
                
            except (ValueError, KeyError) as e:
                _LOGGER.warning(f"Failed to parse record {record}: {e}")
                continue

        if statistics:
            _LOGGER.info(f"Importing {len(statistics)} water usage statistics")
            async_add_external_statistics(self._hass, metadata, statistics)
        else:
            _LOGGER.warning("No valid statistics to import")


class UtilityWaterStatisticsSensor(CoordinatorEntity, SensorEntity):
    """Sensor that displays current water usage and imports statistics."""

    def __init__(
        self,
        coordinator: UtilityWaterDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_has_entity_name = True
        self._attr_name = "Water Usage"
        self._attr_unique_id = f"{config_entry.entry_id}_water_usage"
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfVolume.GALLONS
        self._attr_icon = "mdi:water"
        self._attr_suggested_display_precision = 1

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "Utility Water Meter",
            "manufacturer": "Utility Water Meter",
            "model": "Statistics Import Sensor",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self) -> float | None:
        """Return the current cumulative water usage."""
        if self.coordinator.data:
            # Return the cumulative total as the current sensor state
            value = self.coordinator.data.get("meter_reading", 0)
            _LOGGER.debug(f"Water sensor returning cumulative value: {value} gallons")
            return value
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}
        
        latest_record = self.coordinator.data.get("latest_record", {})
        return {
            "last_updated": latest_record.get("datetime"),
            "latest_hourly_usage": self.coordinator.data.get("latest_hourly", 0),
            "total_records_imported": self.coordinator.data.get("record_count", 0),
            "data_source": "statistics_import",
            "update_interval": "daily",
        }