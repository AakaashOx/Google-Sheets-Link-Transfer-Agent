
import re
from datetime import datetime
from collections import defaultdict


def extract_week_number(task_number):

    match = re.search(r"\d+", str(task_number).strip())

    if not match:
        return None

    return int(match.group())


def normalize_class(class_name):

    value = " ".join(
        str(class_name).strip().upper().split()
    )

    if "AI ML" in value:
        return "BSc AI ML"

    if "AI DS" in value:
        return "BSc AI DS"

    return None


def parse_timestamp(value):

    value = str(value).strip()

    formats = [
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %I:%M:%S %p"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def prepare_unified_submissions(submissions):

    grouped = defaultdict(list)
    skipped = []

    for item in submissions:

        week = extract_week_number(item["task_number"])
        class_name = normalize_class(item["class"])
        reg_no = "".join(
            str(item["reg_no"]).upper().split()
        )
        github_link = str(item["github_link"]).strip()
        timestamp = parse_timestamp(item["timestamp"])

        if week is None:
            skipped.append({
                "record": item,
                "reason": "Invalid Task Number"
            })
            continue

        if class_name is None:
            skipped.append({
                "record": item,
                "reason": "Unrecognized Class"
            })
            continue

        if not reg_no:
            skipped.append({
                "record": item,
                "reason": "Missing Registration Number"
            })
            continue

        if not github_link:
            skipped.append({
                "record": item,
                "reason": "Missing GitHub Link"
            })
            continue

        if timestamp is None:
            skipped.append({
                "record": item,
                "reason": "Invalid Timestamp"
            })
            continue

        key = (class_name, reg_no, week)

        grouped[key].append({
            "week": week,
            "class_name": class_name,
            "reg_no": reg_no,
            "name": item["name"],
            "email": item["email"],
            "github_link": github_link,
            "timestamp": timestamp,
            "original_timestamp": item["timestamp"]
        })

    prepared = []
    duplicate_count = 0
    timestamp_conflicts = []

    for key, records in grouped.items():

        records.sort(
            key=lambda record: record["timestamp"],
            reverse=True
        )

        newest = records[0]

        # Flag identical latest timestamps with different links
        latest_records = [
            record for record in records
            if record["timestamp"] == newest["timestamp"]
        ]

        unique_links = {
            record["github_link"]
            for record in latest_records
        }

        if len(unique_links) > 1:
            timestamp_conflicts.append({
                "class": newest["class_name"],
                "reg_no": newest["reg_no"],
                "week": newest["week"],
                "timestamp": newest["original_timestamp"],
                "links": list(unique_links)
            })
            continue

        prepared.append(newest)

        duplicate_count += len(records) - 1

    return prepared, skipped, duplicate_count, timestamp_conflicts
