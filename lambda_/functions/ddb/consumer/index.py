import json
import os
from time import time, time_ns

execution_ids = []

AWS_EMF_KEY = "_aws"  # change this to disable EMF
MESSAGING_TYPE = os.environ["MESSAGING_TYPE"]


def event_handler(event, context):
    time_now = time_ns()
    consumer_cold_start = len(execution_ids) == 0
    execution_ids.append(context.aws_request_id.lower())

    for record in event["Records"]:
        try:
            data = record["dynamodb"]["NewImage"]
            sent_timestamp_ns = int(data["sent_timestamp_ns"]["N"])
            producer_cold_start = data["producer_cold_start"]["BOOL"]
        except Exception as exc:
            print(f"{type(exc)}: {exc}")
            continue

        duration = time_now - sent_timestamp_ns

        print(
            json.dumps(
                {
                    AWS_EMF_KEY: {
                        "Timestamp": int(time() * 1000),
                        "CloudWatchMetrics": [
                            {
                                "Namespace": "Serverless Messaging",
                                "Dimensions": [
                                    ["Messaging Type", "Cold Start"],
                                ],
                                "Metrics": [
                                    {
                                        "Name": "Latency",
                                        "Unit": "Milliseconds",
                                    },
                                ],
                            }
                        ],
                    },
                    "Messaging Type": MESSAGING_TYPE,
                    "Latency": duration / 1000 / 1000,  # ns to ms
                    "Cold Start": str(
                        consumer_cold_start or producer_cold_start,
                    ),
                }
            )
        )
