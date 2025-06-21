"""Support for Utility Water Meter sensors."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    ATTR_LAST_UPDATED,
    ATTR_TEMPERATURE,
    ATTR_PRECIPITATION,
    ATTR_HUMIDITY,
    ATTR_USAGE_GALLONS,
    SENSOR_WATER_USAGE,
    SENSOR_TEMPERATURE,
    SENSOR_PRECIPITATION,
    SENSOR_HUMIDITY,
    UNIT_PRECIPITATION,
    STATE_CLASS_TOTAL_INCREASING,
    STATE_CLASS_MEASUREMENT,
    DEVICE_CLASS_WATER,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_PRECIPITATION,
    DEVICE_CLASS_HUMIDITY,
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

    # Create sensors
    entities = [
        UtilityWaterUsageSensor(coordinator, config_entry),
        UtilityTemperatureSensor(coordinator, config_entry),
        UtilityPrecipitationSensor(coordinator, config_entry),
        UtilityHumiditySensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class UtilityWaterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the utility meter."""

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
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            data = await self.hass.async_add_executor_job(
                self.scraper.get_latest_data, self.username, self.password
            )
            if not data:
                raise UpdateFailed("Failed to fetch data from utility meter")
            return data
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception


class UtilityWaterBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for utility water sensors."""

    def __init__(
        self,
        coordinator: UtilityWaterDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "Utility Water Meter",
            "manufacturer": "Utility Water Meter",
            "model": "Water Usage Scraper",
            "sw_version": "1.0.0",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None


class UtilityWaterUsageSensor(UtilityWaterBaseSensor):
    """Representation of a water usage sensor."""

    def __init__(
        self,
        coordinator: UtilityWaterDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Water Usage"
        self._attr_unique_id = f"{config_entry.entry_id}_{SENSOR_WATER_USAGE}"
        self._attr_device_class = DEVICE_CLASS_WATER
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfVolume.GALLONS
        self._attr_icon = "mdi:water"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("total_daily_usage")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}
        
        latest_record = self.coordinator.data.get("latest_record", {})
        return {
            ATTR_LAST_UPDATED: latest_record.get("datetime"),
            "latest_hourly_usage": latest_record.get(ATTR_USAGE_GALLONS),
            "record_count": self.coordinator.data.get("record_count"),
        }


class UtilityTemperatureSensor(UtilityWaterBaseSensor):
    """Representation of a temperature sensor."""

    def __init__(
        self,
        coordinator: UtilityWaterDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Temperature"
        self._attr_unique_id = f"{config_entry.entry_id}_{SENSOR_TEMPERATURE}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            latest_record = self.coordinator.data.get("latest_record", {})
            return latest_record.get(ATTR_TEMPERATURE)
        return None


class UtilityPrecipitationSensor(UtilityWaterBaseSensor):
    """Representation of a precipitation sensor."""

    def __init__(
        self,
        coordinator: UtilityWaterDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Precipitation"
        self._attr_unique_id = f"{config_entry.entry_id}_{SENSOR_PRECIPITATION}"
        self._attr_device_class = DEVICE_CLASS_PRECIPITATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UNIT_PRECIPITATION
        self._attr_icon = "mdi:weather-rainy"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            latest_record = self.coordinator.data.get("latest_record", {})
            return latest_record.get(ATTR_PRECIPITATION)
        return None


class UtilityHumiditySensor(UtilityWaterBaseSensor):
    """Representation of a humidity sensor."""

    def __init__(
        self,
        coordinator: UtilityWaterDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = "Humidity"
        self._attr_unique_id = f"{config_entry.entry_id}_{SENSOR_HUMIDITY}"
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            latest_record = self.coordinator.data.get("latest_record", {})
            return latest_record.get(ATTR_HUMIDITY)
        return None