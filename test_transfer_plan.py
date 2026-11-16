from google_sheets import write_transfer_plan

from google_sheets import (
    get_google_sheets_service,
    read_form_responses,
    read_evaluation_roster,
    read_week_link_column
)

from student_matcher import match_submissions_to_roster
from link_transfer import prepare_transfer_plan


def main():

    service = get_google_sheets_service()

    source_url = input(
        "Weekly response spreadsheet URL: "
    ).strip()

    evaluation_url = input("Enter evaluation spreadsheet URL: ").strip()

    week = int(input("Which week are we testing? "))

    if week < 1:
        print("Week number must be at least 1.")
        return

    submissions = read_form_responses(service, source_url)

    if submissions is None:
        print("Invalid source spreadsheet.")
        return

    roster = read_evaluation_roster(
        service,
        evaluation_url,
        "BSc AI ML"
    )

    results = match_submissions_to_roster(
        submissions,
        roster,
        "BSc AI ML"
    )

    existing_links = read_week_link_column(
        service,
        evaluation_url,
        "BSc AI ML",
        week
    )

    transfer = prepare_transfer_plan(
        results["matched"],
        existing_links,
        week
    )

    print("\n========== TRANSFER PREVIEW ==========")
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
        print(item["reg_no"], "-", item["reason"])

    print("\n========== WRITE CONFIRMATION ==========")

    confirmation = input(
        f"Type WRITE WEEK {week} to transfer these links: "
    ).strip()

    if confirmation == f"WRITE WEEK {week}":
        try:
            updated = write_transfer_plan(
                service,
                evaluation_url,
                "BSc AI ML",
                week,
                transfer["plan"]
            )

            inserted = sum(
                1 for item in transfer["plan"]
                if item["action"] == "INSERT"
            )

            replaced = sum(
                1 for item in transfer["plan"]
                if item["action"] == "REPLACE"
            )

            skipped = len(transfer["skipped"])
            failed = max(0, len(transfer["plan"]) - updated)

            print("\n========== TRANSFER REPORT ==========")
            print("Week:", week)
            print("New links inserted:", inserted)
            print("Existing links replaced:", replaced)
            print("Skipped:", skipped)
            print("Failed:", failed)
            print("Successfully updated cells:", updated)
            print("=====================================")
            print("\n========== MATCHING SUMMARY ==========")

            print("Students matched:", len(results["matched"]))
            print("Unmatched submissions:", len(results["unmatched"]))
            print("Duplicate submissions:", len(results["duplicate_submissions"]))
            print("Duplicate roster entries:", len(results["duplicate_roster"]))

            if results["unmatched"]:
                print("\nUnmatched records:")

                for item in results["unmatched"]:
                    print(
                        item.get("reg_no", "Unknown"),
                        "-",
                        item.get("reason", "Not matched")
                    )

            if results["duplicate_submissions"]:
                print("\nDuplicate submissions:")

                for reg_no in results["duplicate_submissions"]:
                    print(reg_no)

            if results["duplicate_roster"]:
                print("\nDuplicate roster entries:")

                for reg_no in results["duplicate_roster"]:
                    print(reg_no)







            

        except Exception as error:
            print("\nTransfer failed:", error)
    else:
        print("\nCancelled. No spreadsheet cells were modified.")


if __name__ == "__main__":
    main()
