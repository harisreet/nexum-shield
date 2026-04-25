import os
import requests

PUBSUB_URL = "http://localhost:8085"
PROJECT = "nexum-local"
TOPIC = "media-events"
SUB = "media-worker-sub"
PUSH_ENDPOINT = "http://localhost:8002/process"

print(f"Creating topic '{TOPIC}'...")
requests.put(f"{PUBSUB_URL}/v1/projects/{PROJECT}/topics/{TOPIC}")

print(f"Creating subscription '{SUB}' pushing to {PUSH_ENDPOINT}...")
response = requests.put(
    f"{PUBSUB_URL}/v1/projects/{PROJECT}/subscriptions/{SUB}",
    json={
        "topic": f"projects/{PROJECT}/topics/{TOPIC}",
        "pushConfig": {"pushEndpoint": PUSH_ENDPOINT}
    }
)
print("Done! Emulators are ready.")
