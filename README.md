
# Water Meters Monitoring System

## Tinybird

### Overview
This project provides a real-time monitoring system for water meters, tracking metrics such as temperature and flow rate. The system ingests data from Kafka and provides API endpoints to query the latest measurements and daily averages for specific sensors.

### Data Sources

#### kafka_water_meters
This data source ingests water meter metrics from a Kafka topic. It captures temperature, flow rate, meter ID, and timestamp information.

To ingest sample data (for testing purposes):
```bash
curl -X POST "https://api.europe-west2.gcp.tinybird.co/v0/events?name=kafka_water_meters" \
     -H "Authorization: Bearer $TB_ADMIN_TOKEN" \
     -d '{"meter_id": 1, "timestamp": "2023-09-15 10:30:00", "flow_rate": 1.8, "temperature": 22.5}'
```

### Endpoints

#### meter_measurements
This endpoint returns the latest value and today's average for a specified sensor and measurement type (temperature or flow_rate).

**Parameters:**
- `sensor_id` (Int32): The ID of the meter to query (default: 1)
- `measurement` (String): The type of measurement to retrieve - either "temperature" or "flow_rate" (default: "temperature")

**Usage:**
```bash
curl -X GET "https://api.europe-west2.gcp.tinybird.co/v0/pipes/meter_measurements.json?token=$TB_ADMIN_TOKEN&sensor_id=1&measurement=temperature"
```

This will return the latest temperature value and today's average temperature for sensor ID 1.

Example response:
```json
{
  "data": [
    {
      "meter_id": 1,
      "measurement": "temperature",
      "latest_value": 22.5,
      "today_avg": 21.8
    }
  ],
  "meta": [
    {
      "name": "meter_id",
      "type": "Int32"
    },
    {
      "name": "measurement",
      "type": "String"
    },
    {
      "name": "latest_value",
      "type": "Float32"
    },
    {
      "name": "today_avg",
      "type": "Float64"
    }
  ],
  "rows": 1,
  "statistics": {
    "elapsed": 0.004866666,
    "rows_read": 10,
    "bytes_read": 80
  }
}
```

To query flow rate data:
```bash
curl -X GET "https://api.europe-west2.gcp.tinybird.co/v0/pipes/meter_measurements.json?token=$TB_ADMIN_TOKEN&sensor_id=1&measurement=flow_rate"
```
