
from collections import Counter

from google_sheets import get_google_sheets_service
from unified_transfer import read_unified_responses
from unified_matcher import prepare_unified_submissions


source_url = input("Enter central Google Sheets URL: ").strip()

service = get_google_sheets_service()

submissions = read_unified_responses(service, source_url)

prepared, skipped, duplicates, conflicts = (
    prepare_unified_submissions(submissions)
)

print("\n========== LATEST SUBMISSION TEST ==========")

print("Original submissions:", len(submissions))
print("Latest submissions retained:", len(prepared))
print("Older submissions discarded:", duplicates)
print("Skipped records:", len(skipped))
print("Timestamp conflicts:", len(conflicts))

print("\nWeeks detected:")

week_counts = Counter(item["week"] for item in prepared)

for week in sorted(week_counts):
    print(f"Week {week}: {week_counts[week]}")

print("\nClasses detected:")

class_counts = Counter(item["class_name"] for item in prepared)

for class_name, count in class_counts.items():
    print(f"{class_name}: {count}")

if conflicts:
    print("\nTimestamp conflicts requiring review:")
    for conflict in conflicts:
        print(conflict)

if skipped:
    print("\nSkipped records:")
    for item in skipped:
        print(item["reason"], item["record"])

print("\n========== TEST COMPLETED ==========")
