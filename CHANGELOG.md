# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-20

### Added
- Initial release of City Water Utility Data Scraper
- Automated login to utilitybilling.lawrenceks.gov
- Hourly water usage data extraction with weather correlation
- CSV export functionality
- Proper logging system with configurable levels
- Command-line interface with multiple usage options
- Environment-based configuration management
- CSRF token handling for secure authentication
- Rate limiting to respect server resources
- Debug utilities for troubleshooting authentication issues

### Features
- **Data Extraction**: Retrieve hourly water usage data from embedded JavaScript
- **Weather Data**: Includes temperature, precipitation, and humidity data
- **CSV Export**: Save structured data to timestamped CSV files
- **CLI Interface**: Easy-to-use command-line tool with help documentation
- **Configuration**: Flexible environment variable configuration
- **Authentication**: Robust login handling with redirect management
- **Error Handling**: Comprehensive error handling and logging
- **Package Structure**: Professional Python package layout with src/ structure

### Technical Details
- Python 3.7+ compatibility
- Uses requests, BeautifulSoup4, and python-dotenv
- Follows PEP 8 coding standards
- MIT licensed
- Comprehensive documentation and examples

### Project Structure
```
myMeterData/
├── README.md              # Project documentation
├── LICENSE                # MIT license
├── CHANGELOG.md           # This file
├── pyproject.toml         # Modern Python packaging
├── requirements.txt       # Dependencies
├── .env.example          # Configuration template
├── .gitignore            # Git ignore patterns
├── src/
│   └── my_meter_data/    # Main package
│       ├── __init__.py   # Package initialization
│       ├── scraper.py    # Core scraping functionality
│       └── cli.py        # Command-line interface
├── scripts/
│   ├── scrape_usage.py   # Standalone CLI script
│   └── debug_login.py    # Authentication debugging
├── docs/
│   └── ENDPOINTS.md      # API endpoint documentation
├── data/                 # Output directory for CSV files
└── reference/            # Reference materials
```

### Usage Examples
```bash
# Using the standalone script
python scripts/scrape_usage.py

# With custom configuration
python scripts/scrape_usage.py --config /path/to/.env --debug

# After pip install (future feature)
scrape-usage --help
```

### Data Format
The scraper outputs CSV files with the following structure:
- `datetime`: Hour-by-hour time periods
- `usage_gallons`: Water consumption in gallons
- `temperature_f`: Temperature in Fahrenheit
- `precipitation_in`: Precipitation in inches
- `humidity_percent`: Relative humidity percentage