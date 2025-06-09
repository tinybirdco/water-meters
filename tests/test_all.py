import os
import subprocess
import time
import requests
import yaml
import pytest
import json
import glob

# Get the absolute path to the tb command
TB_COMMAND = "/Users/gnz-tb/.local/bin/tb"

def load_test_cases(yaml_file):
    """Load test cases from a YAML file."""
    with open(yaml_file, 'r') as f:
        return yaml.safe_load(f)

def run_command(command, input_data=None):
    """Run a command with detailed logging."""
    print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            input=input_data
        )
        print(f"Command output: {result.stdout}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {' '.join(command)}")
        print(f"Error output: {e.stderr}")
        raise
    except Exception as e:
        print(f"Unexpected error running command {' '.join(command)}: {str(e)}")
        raise

def get_token_and_host():
    """Get the token and host for API authentication."""
    print("\nGetting API token and host...")
    result = run_command([TB_COMMAND, "--output", "json", "info"])
    data = json.loads(result)
    token = data["local"]["token"]
    host = data["local"]["api"]
    print(f"Got token: {token[:10]}...")
    print(f"Got host: {host}")
    return token, host

def run_test_cases(endpoint, test_cases, base_url, token):
    """Run test cases for a specific endpoint."""
    print(f"\nTesting {endpoint} endpoint...")
    url = f"{base_url}/{endpoint}.ndjson"
    
    for test_case in test_cases:
        print(f"\nRunning test case: {test_case['name']}")
        
        # Prepare parameters
        params = {"token": token}
        if test_case.get("parameters"):
            params.update(dict(param.split("=") for param in test_case["parameters"].split("&")))
        
        # Make request
        print(f"Making request to {url} with params: {params}")
        response = requests.get(url, params=params)
        
        # Check HTTP status
        expected_status = test_case.get("expected_http_status", 200)
        assert response.status_code == expected_status, \
            f"Test '{test_case['name']}' failed: Expected status {expected_status}, got {response.status_code}"
        
        # Check response content
        if test_case["expected_result"]:
            if expected_status == 400:
                # For error responses, check the error message directly
                error_data = response.json()
                assert error_data["error"] == test_case["expected_result"], \
                    f"Test '{test_case['name']}' failed: Expected error '{test_case['expected_result']}', got '{error_data['error']}'"
            else:
                # For successful responses, parse as NDJSON
                expected_data = [json.loads(line) for line in test_case["expected_result"].strip().split('\n') if line.strip()]
                actual_data = [json.loads(line) for line in response.text.strip().split('\n') if line.strip()]
                print(f"Expected data: {expected_data}")
                print(f"Actual data: {actual_data}")
                assert actual_data == expected_data, \
                    f"Test '{test_case['name']}' failed: Expected {expected_data}, got {actual_data}"

def test_all_endpoints():
    """Test all endpoints using their respective YAML test files."""
    try:
        print("\n=== Setting up test environment ===")
        
        # Clear workspace
        print("\nClearing workspace...")
        run_command([TB_COMMAND, "workspace", "clear", "--yes"])
        
        # Deploy the project
        print("\nDeploying project...")
        run_command([TB_COMMAND, "deploy"])
        
        # Send test data to Redpanda
        print("\nSending test data to Redpanda...")
        with open("fixtures/kafka_water_meters.ndjson", "r") as f:
            data = f.read()
            run_command(["docker", "exec", "-i", "redpanda", "rpk", "topic", "produce", "water_metrics_demo", "-X", "brokers=redpanda:9092"], input_data=data)
        
        # Wait for data to be ingested
        print("\nWaiting for data ingestion...")
        time.sleep(45)  # Increased wait time
        
        print("\n=== Starting endpoint tests ===")
        
        # Get API token and host
        token, host = get_token_and_host()
        base_url = f"{host}/v0/pipes"
        
        # Find all YAML test files in the tests directory
        test_files = glob.glob("tests/*.yaml")
        
        # Run tests for each YAML file
        for test_file in test_files:
            # Extract endpoint name from filename (remove .yaml extension)
            endpoint = os.path.splitext(os.path.basename(test_file))[0]
            test_cases = load_test_cases(test_file)
            run_test_cases(endpoint, test_cases, base_url, token)
    
    finally:
        # Cleanup
        print("\n=== Cleaning up test environment ===")
        # run_command([TB_COMMAND, "workspace", "clear", "--yes"]) 