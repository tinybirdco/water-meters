#!/bin/bash

# Function to check if Redpanda is ready
check_redpanda_health() {
    local health_output
    health_output=$(docker exec -i redpanda rpk cluster health --format json)
    if [[ $health_output == *"\"is_healthy\":true"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to check if Tinybird is ready
check_tinybird_status() {
    local status_output
    status_output=$(tb --output json info)
    if [[ $status_output == *"\"local\""* ]]; then
        return 0
    else
        return 1
    fi
}

# Maximum number of retries
MAX_RETRIES=30
RETRY_INTERVAL=5

# Wait for both Redpanda and Tinybird to be ready
echo "Waiting for both Redpanda and Tinybird Local to be ready..."

# Try until success or max retries reached
for ((i=1; i<=MAX_RETRIES; i++)); do
    if check_redpanda_health && check_tinybird_status; then
        echo "✓ Both Redpanda and Tinybird Local are ready!"
        echo "Proceeding with deployment..."
        # Create topic in Redpanda
        docker exec -i redpanda rpk topic create water_metrics_demo -X brokers=redpanda:9092
        # Deploy to Tinybird
        tb deploy
        # Produce to Redpanda topic
        cat fixtures/kafka_water_meters.ndjson | docker exec -i redpanda rpk topic produce water_metrics_demo -X brokers=redpanda:9092
        # Execute SQL query in Tinybird
        tb sql "select meter_id, timestamp, flow_rate, temperature from kafka_water_meters"
        echo -e "\n✅ Setup completed successfully!"
        return 0
    else
        echo "Attempt $i/$MAX_RETRIES: Tinybird Local not ready yet. Waiting ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
    fi
done

echo "❌ Failed to connect to Redpanda and Tinybird Local after $MAX_RETRIES attempts"
return 1