
from collections import Counter

from google_sheets import get_google_sheets_service
from unified_transfer import read_unified_responses


def main():

    source_url = input(
        "Enter central Google Sheets URL: "
    ).strip()

    service = get_google_sheets_service()

    submissions = read_unified_responses(
        service,
        source_url
    )

    print("\n========== READ TEST REPORT ==========")

    print("Total submissions:", len(submissions))

    task_counts = Counter(
        str(item["task_number"]).strip() or "MISSING"
        for item in submissions
    )

    class_counts = Counter(
        str(item["class"]).strip() or "MISSING"
        for item in submissions
    )

    print("\nSubmissions by Task Number:")

    for task, count in sorted(task_counts.items()):
        print(f"Task {task}: {count}")

    print("\nSubmissions by Class:")

    for class_name, count in class_counts.items():
        print(f"{class_name}: {count}")

    missing_reg = sum(
        not str(item["reg_no"]).strip()
        for item in submissions
    )

    missing_task = sum(
        not str(item["task_number"]).strip()
        for item in submissions
    )

    missing_links = sum(
        not str(item["github_link"]).strip()
        for item in submissions
    )

    print("\nData checks:")
    print("Missing Registration Numbers:", missing_reg)
    print("Missing Task Numbers:", missing_task)
    print("Missing GitHub Links:", missing_links)

    print("\n========== TEST COMPLETED ==========")


if __name__ == "__main__":
    main()
