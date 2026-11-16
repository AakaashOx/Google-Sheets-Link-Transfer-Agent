
from google_sheets import extract_spreadsheet_id


def read_unified_responses(service, source_url):

    # Extract the spreadsheet ID from the URL
    spreadsheet_id = extract_spreadsheet_id(source_url)

    # Identify the first worksheet tab automatically
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties.title"
    ).execute()

    sheets = spreadsheet.get("sheets", [])

    if not sheets:
        raise ValueError("The source spreadsheet has no worksheet tabs.")

    sheet_name = sheets[0]["properties"]["title"]

    # Read all columns from the first worksheet
    safe_sheet_name = sheet_name.replace("'", "''")

    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{safe_sheet_name}'!A:Z"
    ).execute()

    values = response.get("values", [])

    if not values:
        raise ValueError("The source spreadsheet is empty.")

    # Normalize headers to handle extra spaces and capitalization
    headers = [
        " ".join(str(header).strip().lower().split())
        for header in values[0]
    ]

    required_headers = [
        "timestamp",
        "email address",
        "name",
        "class",
        "reg no",
        "task number",
        "github link"
    ]

    missing_headers = [
        header for header in required_headers
        if header not in headers
    ]

    if missing_headers:
        raise ValueError(
            f"Missing required columns: {missing_headers}"
        )

    # Read submissions
    submissions = []

    for row in values[1:]:

        row = row + [""] * (len(headers) - len(row))

        record = dict(zip(headers, row))

        # Skip completely empty rows
        if not any(str(value).strip() for value in row):
            continue

        submissions.append({
            "timestamp": record["timestamp"],
            "email": record["email address"],
            "name": record["name"],
            "class": record["class"],
            "reg_no": record["reg no"],
            "task_number": record["task number"],
            "github_link": record["github link"]
        })

    return submissions
