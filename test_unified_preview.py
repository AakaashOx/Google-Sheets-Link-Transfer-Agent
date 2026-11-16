from google_sheets import write_transfer_plan
from google_sheets import get_google_sheets_service
from unified_transfer import read_unified_responses
from unified_matcher import prepare_unified_submissions
from unified_preview import prepare_unified_preview


def main():

    source_url = input(
        "Enter central responses spreadsheet URL: "
    ).strip()

    evaluation_url = input(
        "Enter evaluation spreadsheet URL: "
    ).strip()

    service = get_google_sheets_service()

    print("\nReading central responses...")

    submissions = read_unified_responses(
        service, source_url
    )

    prepared, skipped, duplicates, conflicts = (
        prepare_unified_submissions(submissions)
    )

    print("Latest submissions:", len(prepared))
    print("Older submissions discarded:", duplicates)

    if skipped or conflicts:
        print("Skipped records:", len(skipped))
        print("Timestamp conflicts:", len(conflicts))
        print("Fix these data issues before transferring.")
        return

    # Start with Week 1 only
    selected_weeks = [12]
    
    print("\nPreparing Week 1 preview...")

    preview = prepare_unified_preview(
        service,
        evaluation_url,
        prepared,
        selected_weeks
    )

    print("\n========== TRANSFER PREVIEW ==========")

    print("Selected weeks:", preview["selected_weeks"])

    for entry in preview["results"]:

        print("\nClass:", entry["class_name"])
        print("Week:", entry["week"])

        result = entry["result"]
        transfer = result["transfer"]

        plan = transfer["plan"]
        skipped_records = transfer["skipped"]

        print("Planned updates:", len(plan))
        print("Skipped records:", len(skipped_records))

        print("Full transfer details:")
        print(transfer)

        for item in plan:
            print(item)

    print("\n========== WRITE CONFIRMATION ==========")

    confirmation = input(
        "Type WRITE WEEK 1 to transfer these links: "
    ).strip()

    if confirmation == "WRITE WEEK 1":

        for entry in preview["results"]:

            result = entry["result"]
            plan = result["transfer"]["plan"]

            updated = write_transfer_plan(
                service,
                evaluation_url,
                entry["class_name"],
                entry["week"],
                plan
            )

            print(
                f"Week {entry['week']} - "
                f"{entry['class_name']}: "
                f"{updated} cells updated."
            )

        print("\nTRANSFER COMPLETED.")

    else:
        print("\nTransfer cancelled. No data was written.")




    print("\n========== PREVIEW COMPLETED ==========")
    print("NO DATA WAS WRITTEN TO GOOGLE SHEETS.")


if __name__ == "__main__":
    main()
