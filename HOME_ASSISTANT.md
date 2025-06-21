# Home Assistant Integration: Utility Water Meter

This Home Assistant integration allows you to track your water usage from utility billing systems directly in your Home Assistant Energy dashboard.

## Features

- **Water Usage Tracking**: Monitor daily and hourly water consumption
- **Energy Dashboard Integration**: Water usage appears in Home Assistant's Energy page
- **Weather Correlation**: Track temperature, precipitation, and humidity alongside usage
- **Automatic Updates**: Configurable update intervals (default: 1 hour)
- **HACS Compatible**: Easy installation and updates through HACS

## Installation

### Method 1: HACS (Recommended)

1. **Install HACS** if you haven't already: [HACS Installation Guide](https://hacs.xyz/docs/setup/download)

2. **Add Custom Repository**:
   - Go to HACS → Integrations
   - Click the three dots menu → Custom repositories
   - Add repository URL: `https://github.com/yourusername/myMeterData`
   - Category: Integration
   - Click "Add"

3. **Install Integration**:
   - Search for "Utility Water Meter" in HACS
   - Click "Download"
   - Restart Home Assistant

### Method 2: Manual Installation

1. **Download Integration**:
   ```bash
   cd /config/custom_components
   git clone https://github.com/yourusername/myMeterData.git
   cp -r myMeterData/custom_components/utility_water ./
   ```

2. **Restart Home Assistant**

## Configuration

### Setup Integration

1. **Add Integration**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Utility Water Meter"
   - Click to add

2. **Enter Credentials**:
   - **Username**: Your utility billing system email
   - **Password**: Your utility billing system password
   - **Base URL**: (Usually auto-filled, change if needed)
   - **Update Interval**: How often to fetch data (hours)

3. **Complete Setup**:
   - Click "Submit"
   - Integration will test connection and create sensors

### Sensors Created

The integration creates these sensors:

| Sensor | Description | Unit | Device Class |
|--------|-------------|------|--------------|
| `sensor.utility_water_meter_water_usage` | Daily water consumption | gallons | water |
| `sensor.utility_water_meter_temperature` | Current temperature | °F | temperature |
| `sensor.utility_water_meter_precipitation` | Precipitation | inches | precipitation |
| `sensor.utility_water_meter_humidity` | Humidity | % | humidity |

### Energy Dashboard Setup

1. **Add Water Source**:
   - Go to Settings → Dashboards → Energy
   - Click "Add Water Source"
   - Select `sensor.utility_water_meter_water_usage`
   - Click "Save"

2. **Configure**:
   - The sensor uses `state_class: total_increasing` for proper Energy dashboard integration
   - Water usage will now appear in your Energy dashboard

## Usage Examples

### Automation Example

```yaml
automation:
  - alias: "High Water Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.utility_water_meter_water_usage
        above: 100  # Alert if daily usage exceeds 100 gallons
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "High water usage detected: {{ states('sensor.utility_water_meter_water_usage') }} gallons today"
```

### Template Sensor for Hourly Usage

```yaml
template:
  - sensor:
      - name: "Hourly Water Usage"
        unit_of_measurement: "gal"
        state: "{{ state_attr('sensor.utility_water_meter_water_usage', 'latest_hourly_usage') }}"
        device_class: water
```

### Dashboard Card Example

```yaml
type: entities
entities:
  - entity: sensor.utility_water_meter_water_usage
    name: Daily Usage
  - entity: sensor.utility_water_meter_temperature
    name: Temperature
  - entity: sensor.utility_water_meter_humidity
    name: Humidity
title: Water Usage
```

## Troubleshooting

### Common Issues

**Integration Not Loading**:
- Check Home Assistant logs: Settings → System → Logs
- Ensure all files are in `/config/custom_components/utility_water/`
- Restart Home Assistant after installation

**Login Failures**:
- Verify credentials in the utility billing website
- Check if 2FA is enabled (not currently supported)
- Review integration logs for specific error messages

**No Data Appearing**:
- Check update interval (may take time for first data)
- Verify utility website is accessible
- Look for rate limiting or blocking

### Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.utility_water: debug
```

### Manual Data Refresh

Use the service call to manually refresh data:

```yaml
service: utility_water.refresh_data
```

## Supported Systems

Currently supports:
- Your city utility billing system (configurable base URL)

The integration can be adapted for other utility systems with similar authentication flows.

## Data Privacy

- Credentials are stored locally in Home Assistant
- No data is sent to external services beyond the utility website
- All communication is direct between Home Assistant and your utility provider

## Contributing

See the main [README.md](README.md) for development setup and contribution guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/myMeterData/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/myMeterData/discussions)
- **Home Assistant Community**: Tag `@yourusername` in Home Assistant forums

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.