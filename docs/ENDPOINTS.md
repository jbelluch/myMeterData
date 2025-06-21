# City Utility Billing API Endpoints

Based on analysis of the dashboard HTML, here are the key endpoints used to fetch utility data:

## Base URL
`https://utilitybilling.lawrenceks.gov`

## Key Data Endpoints

### 1. Dashboard Table Data
- **URL**: `/Dashboard/Table`
- **Method**: GET (via AJAX)
- **Description**: Returns tabular usage data
- **Authentication**: Session-based (requires login)
- **Response**: JSON or HTML with usage table

### 2. Dashboard Chart Data  
- **URL**: `/Dashboard/Chart`
- **Method**: GET (via AJAX)
- **Description**: Returns chart/graph data for usage visualization
- **Authentication**: Session-based (requires login)
- **Response**: JSON with chart data

### 3. Property Information
- **URL**: `/Dashboard/Property`
- **Method**: GET (via AJAX)
- **Description**: Returns property-specific information
- **Authentication**: Session-based (requires login)

### 4. Usage Data Export
- **URL**: `/Usage/InitializeDownloadSettings`
- **Method**: GET
- **Description**: Initializes export settings
- **Follow-up**: Call export endpoint after initialization

### 5. Widget Data
- **URL**: `/Widget/LoadWidgets?Region=Usage`
- **Method**: GET
- **Description**: Loads usage widgets/summary data

## Authentication Requirements

- Session-based authentication using cookies
- Login through `/Account/Login` endpoint
- Requires valid username/password
- CSRF tokens may be required (look for `__RequestVerificationToken`)

## Headers Required

```
User-Agent: Mozilla/5.0 (compatible browser string)
Accept: application/json, text/javascript, */*; q=0.01
X-Requested-With: XMLHttpRequest
Referer: https://utilitybilling.lawrenceks.gov/Dashboard
```

## JavaScript Function

The site uses a `processAjax()` function for all AJAX calls with these common parameters:
- `url`: The endpoint URL
- `loadingContainer`: DOM element to show loading state
- `success`: Callback function for successful response
- `messageContainer`: DOM element for error messages

## Notes

1. All data endpoints require active authentication session
2. The site uses anti-CSRF tokens for state-changing operations
3. Some endpoints may return HTML that needs parsing vs. pure JSON
4. Rate limiting may be in place - add delays between requests
5. The site tracks analytics via Google Tag Manager for dashboard interactions

## Next Steps

1. Implement login mechanism with CSRF token extraction
2. Test each endpoint to understand response format
3. Add HTML parsing for endpoints that return HTML instead of JSON
4. Implement proper session management and cookie handling