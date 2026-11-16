
def normalize_value(value):
    """Standardize registration numbers and class names."""
    return "".join(str(value).split()).upper()


def match_submissions_to_roster(submissions, roster_rows, target_class):
    """
    Match form submissions against the evaluation sheet roster.

    Form columns:
    A Timestamp, B Email, C Name, D Class, E Reg No, F GitHub Link

    Roster columns:
    A Sl. No., B Roll No., C Student Name
    """

    target_class = normalize_value(target_class)

    # Build a registration-number lookup from the evaluation sheet.
    roster_lookup = {}
    duplicate_roster = set()

    for sheet_row, row in enumerate(roster_rows, start=5):
        if len(row) < 2:
            continue

        reg_no = normalize_value(row[1])

        if not reg_no:
            continue

        if reg_no in roster_lookup:
            duplicate_roster.add(reg_no)
        else:
            roster_lookup[reg_no] = {
                "row": row,
                "sheet_row": sheet_row
            }

    matched = []
    unmatched = []
    duplicate_submissions = set()
    seen_submissions = set()

    for row in submissions:

        # Ensure all six columns are available.
        row = row + [""] * (6 - len(row))

        student_class = normalize_value(row[3])
        reg_no = normalize_value(row[4])

        if student_class != target_class:
            continue

        if not reg_no:
            unmatched.append({
                "reason": "Missing registration number"
            })
            continue

        if reg_no in seen_submissions:
            duplicate_submissions.add(reg_no)
            continue

        seen_submissions.add(reg_no)

        if reg_no in duplicate_roster:
            unmatched.append({
                "reg_no": reg_no,
                "reason": "Duplicate registration number in roster"
            })
            continue

        if reg_no not in roster_lookup:
            unmatched.append({
                "reg_no": reg_no,
                "reason": "Student not found in evaluation roster"
            })
            continue

        student = roster_lookup[reg_no]

        matched.append({
            "reg_no": reg_no,
            "student_name": student["row"][2]
                if len(student["row"]) > 2 else "",
            "destination_row": student["sheet_row"],
            "github_link": row[5]
        })

    # Remove any student with multiple submissions from automatic matching.
    matched = [
        student for student in matched
        if student["reg_no"] not in duplicate_submissions
    ]

    return {
        "matched": matched,
        "unmatched": unmatched,
        "duplicate_submissions": sorted(duplicate_submissions),
        "duplicate_roster": sorted(duplicate_roster)
    }
