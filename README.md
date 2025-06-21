# Utility Water Meter Data Tool

A comprehensive Python tool and Home Assistant integration to extract and analyze water usage data from utility billing systems.

## 🏠 Home Assistant Integration

**NEW**: This project now includes a full Home Assistant integration! Track your water usage directly in the Energy dashboard.

### Quick Start for Home Assistant

- Install via HACS (Home Assistant Community Store)
- Configure with your utility credentials
- Water usage appears in Energy dashboard automatically
- See [HOME_ASSISTANT.md](HOME_ASSISTANT.md) for detailed setup

## 🐍 Python CLI Tool Features

- **Automated Login**: Securely authenticate with the utility billing system
- **Data Extraction**: Retrieve hourly water usage data with weather correlations
- **CSV Export**: Save usage data to CSV files for analysis
- **Weather Data**: Includes temperature, precipitation, and humidity data
- **Rate Limiting**: Built-in delays to respect server resources
- **Home Assistant Ready**: Use as standalone tool or HA integration

## Installation

### 🏠 Home Assistant Integration

For Home Assistant users, see the dedicated [Home Assistant Setup Guide](HOME_ASSISTANT.md) for HACS installation and Energy dashboard configuration.

### 🐍 Python CLI Tool

#### Prerequisites

- Python 3.7 or higher
- pip package manager

#### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jbelluch/myMeterData.git
   cd myMeterData
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file:**

   ```bash
   cp .env.example .env
   ```

4. **Configure credentials:**
   Edit `.env` and add your utility account credentials:
   ```
   UTILITY_USERNAME=your_email@example.com
   UTILITY_PASSWORD=your_password
   ```

## Usage

### Basic Usage

Run the scraper to extract your water usage data:

```bash
python utility_scraper.py
```

The script will:

1. Login to your utility account
2. Retrieve dashboard data
3. Extract usage information
4. Save hourly usage data to `./data/water_usage_YYYYMMDD_HHMMSS.csv`

### Output Format

The CSV file contains the following columns:

| Column             | Description                                                    |
| ------------------ | -------------------------------------------------------------- |
| `datetime`         | Hour time period (e.g., "Thu, Jun 19, 2025 4:00 AM - 5:00 AM") |
| `usage_gallons`    | Water consumption in gallons for that hour                     |
| `temperature_f`    | Average temperature in Fahrenheit                              |
| `precipitation_in` | Precipitation in inches                                        |
| `humidity_percent` | Relative humidity percentage                                   |

### Example Output

```csv
datetime,usage_gallons,temperature_f,precipitation_in,humidity_percent
"Thu, Jun 19, 2025 4:00 AM - 5:00 AM",73.0,61,0.0,99.0
"Thu, Jun 19, 2025 5:00 AM - 6:00 AM",16.0,59,0.0,99.0
"Thu, Jun 19, 2025 6:00 AM - 7:00 AM",2.0,61,0.0,99.0
```

## Configuration

### Environment Variables

Configure the scraper by editing `.env`:

```bash
# Lawrence KS Utility Billing Credentials
UTILITY_USERNAME=your_email@example.com
UTILITY_PASSWORD=your_password

# Base URL (shouldn't need to change)
BASE_URL=https://utilitybilling.lawrenceks.gov

# Export settings
DEFAULT_EXPORT_FORMAT=csv
OUTPUT_DIRECTORY=./data

# Request settings (in seconds)
REQUEST_DELAY=1.0
TIMEOUT=30
```

### Customization

- **Output Directory**: Change `OUTPUT_DIRECTORY` to save files elsewhere
- **Request Timing**: Adjust `REQUEST_DELAY` and `TIMEOUT` as needed
- **Export Format**: Currently supports CSV format

## Project Structure

```
myMeterData/
├── README.md                     # Main documentation
├── HOME_ASSISTANT.md            # Home Assistant setup guide
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT license
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Modern Python packaging
├── .env.example                # Environment template
├── .gitignore                  # Git ignore patterns
├── hacs.json                   # HACS integration info
├── custom_components/          # Home Assistant integration
│   └── utility_water/         # Integration files
│       ├── __init__.py        # Integration initialization
│       ├── manifest.json      # Integration metadata
│       ├── config_flow.py     # Setup UI flow
│       ├── sensor.py          # Water usage sensors
│       ├── scraper.py         # HA-optimized scraper
│       ├── const.py          # Constants
│       ├── services.yaml     # Service definitions
│       └── translations/     # UI translations
├── src/                       # Python package source
│   └── my_meter_data/        # Main package
│       ├── __init__.py       # Package initialization
│       ├── scraper.py        # Core scraping functionality
│       └── cli.py            # Command-line interface
├── scripts/                  # Utility scripts
│   ├── scrape_usage.py      # Standalone CLI script
│   └── debug_login.py       # Authentication debugging
├── docs/                    # Documentation
│   └── ENDPOINTS.md         # API endpoint documentation
├── data/                    # Output directory for CSV files
└── reference/               # Reference materials
```

## Technical Details

### Authentication

The scraper handles the complex authentication flow:

1. **Homepage Analysis**: Retrieves login form structure
2. **CSRF Protection**: Extracts and includes required tokens
3. **Session Management**: Maintains authenticated session cookies
4. **Redirect Handling**: Follows authentication redirects properly

### Data Parsing

Water usage data is embedded in the dashboard as JavaScript `tooltipJSON`. The scraper:

1. Extracts HTML content from AJAX responses
2. Uses regex to locate embedded JSON data
3. Parses tooltip data containing usage and weather information
4. Converts to structured CSV format

## Troubleshooting

### Common Issues

**Login Failures:**

- Verify credentials in `.env` file
- Check if account requires 2FA (not currently supported)
- Run `debug_login.py` for detailed authentication analysis

**No Data Retrieved:**

- Ensure account has usage history
- Check internet connection
- Verify utility website is accessible

**Permission Errors:**

- Ensure `./data/` directory is writable
- Check file permissions

### Debug Mode

For detailed login analysis, run:

```bash
python debug_login.py
```

This provides step-by-step authentication debugging with detailed HTTP logs.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Legal & Ethical Use

This tool is intended for accessing your own utility data. Please:

- Only use with your own utility account
- Respect the utility company's terms of service
- Use reasonable request delays to avoid server overload
- Do not share account credentials

## Disclaimer

This project is not affiliated with the City of Lawrence, Kansas or their utility billing system. Use at your own risk and ensure compliance with the utility company's terms of service.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or issues:

1. Check existing [GitHub Issues](https://github.com/jbelluch/myMeterData/issues)
2. Create a new issue with detailed information
3. Include debug output when reporting problems
