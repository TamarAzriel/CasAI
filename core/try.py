import requests
import time
import sys

# --- Configuration ---
# 1. Put your API Key here
API_KEY = "לשנות פה פשוט"

# Base URL for the API
BASE_URL = "https://api.nanobananaapi.ai"


# Helper to get necessary headers
def get_headers():
return {
"Authorization": f"Bearer {API_KEY}",
"Content-Type": "application/json"
}


# --- Step 1: Submit the Generation Job ---
def submit_job(prompt):
endpoint = "/api/v1/nanobanana/generate"
url = BASE_URL + endpoint

payload = {
"prompt": prompt,
# Note the specific spelling from API docs "TEXTTOIAMGE"
"type": "TEXTTOIAMGE",
"numImages": 1,
"image_size": "16:9",
# REQUIRED by API spec, but we use a dummy URL because we are polling.
"callBackUrl": "http://localhost:9999/dummy-callback-ignore-me"
}

print(f"[Step 1] Submitting task for: '{prompt}'...")
try:
response = requests.post(url, headers=get_headers(), json=payload)
response.raise_for_status() # Raise error if request failed completely
data = response.json()

if data.get('code') == 200:
task_id = data['data']['taskId']
print(f"Task submitted successfully. ID: {task_id}")
return task_id
else:
print(f"Error submitting task. API Response: {data}")
sys.exit(1)
except Exception as e:
print(f"An exception occurred submitting: {e}")
sys.exit(1)


# --- Step 2: Poll for Results ---
def poll_for_results(task_id):
# The endpoint you provided in the latest docs
endpoint = "/api/v1/nanobanana/record-info"
url = BASE_URL + endpoint

# taskId goes in query parameters for GET requests
params = {"taskId": task_id}

max_attempts = 60 # How many times to check
sleep_time = 5 # Seconds to wait between checks

print(f"[Step 2] Polling for results (Will check for approx {max_attempts * sleep_time / 60} mins)...")

for attempt in range(1, max_attempts + 1):
try:
# Make the GET request to check status
print(f"Checking status (attempt {attempt}/{max_attempts})...", end="\r")
response = requests.get(url, headers=get_headers(), params=params)

if response.status_code != 200:
print(f"\nHTTP Error checking status: {response.status_code}")
time.sleep(sleep_time)
continue

data = response.json()

# Navigate the JSON response based on your docs
result_data = data.get('data', {})
# successFlag: 0-generating, 1-success, 2 or 3-failed
success_flag = result_data.get('successFlag')

if success_flag == 0:
# Still generating, wait and loop again
time.sleep(sleep_time)

elif success_flag == 1:
# SUCCESS!
# The final image URL is usually in 'resultImageUrl' according to docs
image_url = result_data.get('response', {}).get('resultImageUrl')
print("\n" + "=" * 40)
print(" >>> GENERATION COMPLETE <<<")
print("=" * 40)
print(f"Final Image URL: {image_url}")
return image_url

elif success_flag in [2, 3]:
# FAILED
error_msg = result_data.get('errorMessage', 'Unknown error')
print(f"\nGeneration FAILED. Flag: {success_flag}, Reason: {error_msg}")
return None
else:
print(f"\nUnknown status flag received: {success_flag}")
time.sleep(sleep_time)

except requests.exceptions.RequestException as e:
print(f"\nNetwork error during polling: {e}. Retrying...")
time.sleep(sleep_time)
except Exception as e:
print(f"\nAn unexpected error occurred: {e}")
return None

print("\nPolling timed out. The task took too long.")
return None


# --- Main Execution Block ---
if __name__ == "__main__":
# Define your prompt here
MY_PROMPT = "A detailed photograph of a cute robot gardener watering plants in a solarium"

# Run the two-step process
taskId = submit_job(MY_PROMPT)
if taskId:
poll_for_results(taskId)
