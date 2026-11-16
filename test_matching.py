
from google_sheets import (
    get_google_sheets_service,
    extract_spreadsheet_id,
    read_form_responses,
    read_evaluation_roster
)

from student_matcher import match_submissions_to_roster


def main():

    service = get_google_sheets_service()

    print("\n--- SOURCE SPREADSHEET ---")
    source_url = input("Paste weekly response spreadsheet URL: ").strip()

    submissions = read_form_responses(
        service,
        source_url
    )

    if submissions is None:
        print("Could not read valid student submissions.")
        return

    print("\n--- EVALUATION SPREADSHEET ---")
    evaluation_url = input(
        "Paste BSc AI DS evaluation spreadsheet URL: "
    ).strip()

    roster = read_evaluation_roster(
        service,
        evaluation_url,
        "BSc AI DS"
    )

    print("\nRoster students found:", len(roster))

    results = match_submissions_to_roster(
        submissions,
        roster,
        "BSc AI DS"
    )

    print("\n========== MATCHING REPORT ==========")
    print("Successfully matched:", len(results["matched"]))
    print("Unmatched submissions:", len(results["unmatched"]))
    print("Duplicate submissions:", len(results["duplicate_submissions"]))
    print("Duplicate roster numbers:", len(results["duplicate_roster"]))

    print("\nMatching preview (first 5 students):")

    for student in results["matched"][:5]:
        print(
            student["reg_no"],
            "-",
            student["student_name"],
            "- GitHub link detected:",
            bool(student["github_link"])
        )

    print("\nNo spreadsheet data was modified.")


if __name__ == "__main__":
    main()
