
def prepare_transfer_plan(matched_students, existing_links, week):
    """Prepare a transfer preview, including links that need replacing."""

    if week < 1:
        raise ValueError("Week number must be at least 1.")

    link_column_number = 4 + (week - 1) * 2

    def column_letter(number):
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    link_column = column_letter(link_column_number)

    plan = []
    skipped = []

    for student in matched_students:

        row_number = student["destination_row"]
        github_link = str(student["github_link"]).strip()

        if not github_link:
            skipped.append({
                "reg_no": student["reg_no"],
                "reason": "GitHub link is empty"
            })
            continue

        index = row_number - 5

        existing_value = ""

        if index < len(existing_links):
            cell_values = existing_links[index]

            if cell_values:
                existing_value = str(cell_values[0]).strip()

        print(
            f"CHECKING {link_column}{row_number}: "
            f"value={repr(existing_value)}, "
            f"length={len(existing_value)}"
        )

        plan.append({
            "reg_no": student["reg_no"],
            "student_name": student["student_name"],
            "cell": f"{link_column}{row_number}",
            "github_link": github_link,
            "existing_link": existing_value,
            "action": "REPLACE" if existing_value else "INSERT"
        })

    return {
        "plan": plan,
        "skipped": skipped
    }

