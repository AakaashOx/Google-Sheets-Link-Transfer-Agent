
from google_sheets import (
    get_google_sheets_service,
    read_form_responses,
    read_evaluation_roster,
    read_week_link_column
)

from student_matcher import match_submissions_to_roster
from link_transfer import prepare_transfer_plan


CLASSES = {
    "BSc AI DS": "BSc AI DS",
    "BSc AI ML": "BSc AI ML"
}


def process_class(service, submissions, evaluation_url, class_name, week):

    print(f"\n========== PROCESSING {class_name} ==========")

    # Read the correct class roster
    roster = read_evaluation_roster(
        service,
        evaluation_url,
        class_name
    )

    # Match submissions to students in this class
    results = match_submissions_to_roster(
        submissions,
        roster,
        class_name
    )

    print("\n========== MATCHING DIAGNOSTICS ==========")

    print("Total roster students:", len(roster))
    print("Matched students:", len(results["matched"]))
    print("Unmatched students:", len(results["unmatched"]))

    print("\nUnmatched details:")
    for student in results["unmatched"]:
        print(student)

    print("\nDuplicate submissions:")
    print(results["duplicate_submissions"])

    print("\nDuplicate roster:")
    print(results["duplicate_roster"])




    # Read existing links from this same class tab
    existing_links = read_week_link_column(
        service,
        evaluation_url,
        class_name,
        week
    )

    # Prepare the transfer plan
    transfer = prepare_transfer_plan(
        results["matched"],
        existing_links,
        week
    )

    return {
        "class_name": class_name,
        "results": results,
        "transfer": transfer
    }


def print_preview(class_data, week):

    class_name = class_data["class_name"]
    results = class_data["results"]
    transfer = class_data["transfer"]

    print(f"\n========== {class_name} PREVIEW ==========")

    print("Week:", week)
    print("Students matched:", len(results["matched"]))
    print("Links ready to transfer:", len(transfer["plan"]))
    print("Skipped:", len(transfer["skipped"]))

    print("\nDestination cells:")

    for item in transfer["plan"]:
        print(
            item["reg_no"],
            "->",
            item["cell"],
            "| Action:",
            item["action"]
        )

    print("\nSkipped records:")

    for item in transfer["skipped"]:
        print(
            item["reg_no"],
            "-",
            item["reason"]
        )

    print("\nMatching summary:")
    print("Unmatched submissions:", len(results["unmatched"]))
    print("Duplicate submissions:", len(results["duplicate_submissions"]))
    print("Duplicate roster entries:", len(results["duplicate_roster"]))


def main():

    print("========================================")
    print("       GOOGLE SHEETS TRANSFER AGENT")
    print("========================================")

    service = get_google_sheets_service()

    source_url = input(
        "\nWeekly response spreadsheet URL: "
    ).strip()

    evaluation_url = input(
        "Evaluation spreadsheet URL: "
    ).strip()

    try:
        week = int(input("Which week should be updated? ").strip())
    except ValueError:
        print("Please enter a valid week number.")
        return

    if week < 1:
        print("Week number must be at least 1.")
        return

    # Read the weekly form responses only once
    submissions = read_form_responses(
        service,
        source_url
    )

    if submissions is None:
        print("Invalid source spreadsheet. Stopping.")
        return

    # Prepare separate plans for both classes
    all_class_data = []

    for class_name in CLASSES.values():

        class_data = process_class(
            service,
            submissions,
            evaluation_url,
            class_name,
            week
        )

        all_class_data.append(class_data)

    # Display both previews
    print("\n\n========================================")
    print("           COMBINED TRANSFER PREVIEW")
    print("========================================")

    for class_data in all_class_data:
        print_preview(class_data, week)

    total_links = sum(
        len(item["transfer"]["plan"])
        for item in all_class_data
    )

    total_skipped = sum(
        len(item["transfer"]["skipped"])
        for item in all_class_data
    )

    print("\n========== OVERALL SUMMARY ==========")
    print("Week:", week)
    print("Total links ready:", total_links)
    print("Total skipped:", total_skipped)

    print("\nPREVIEW ONLY: No spreadsheet cells were modified.")


if __name__ == "__main__":
    main()
