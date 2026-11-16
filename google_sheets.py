
from pathlib import Path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Read-only access: the agent cannot edit spreadsheet contents.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials" / "credentials.json"
TOKEN_FILE = BASE_DIR / "credentials" / "token.json"


def get_google_sheets_service():
    """Authenticate with Google and return a Sheets API service."""

    credentials = None

    # Reuse an existing login if available.
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    # Refresh an expired login, or ask the user to sign in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"OAuth credentials not found: {CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save the login for future runs.
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

    return build("sheets", "v4", credentials=credentials)


def extract_spreadsheet_id(url_or_id):
    """Accept either a Google Sheets URL or a spreadsheet ID."""

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url_or_id)

    if match:
        return match.group(1)

    # Also allow a plain spreadsheet ID.
    if re.fullmatch(r"[a-zA-Z0-9_-]+", url_or_id):
        return url_or_id

    raise ValueError("That doesn't look like a valid Google Sheets URL or ID.")


def test_spreadsheet_connection(service, url_or_id):
    """Read spreadsheet details only. Does not read or modify student data."""

    spreadsheet_id = extract_spreadsheet_id(url_or_id)

    result = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="properties.title,sheets.properties.title"
    ).execute()

    title = result["properties"]["title"]
    sheet_tabs = [
        sheet["properties"]["title"]
        for sheet in result.get("sheets", [])
    ]

    print("\nGoogle Sheets connection successful!")
    print(f"Spreadsheet: {title}")
    print("Tabs found:")

    for tab in sheet_tabs:
        print(f" - {tab}")


def read_form_responses(service, url_or_id, sheet_name="Form Responses 1"):
    """Read student submission data without modifying the spreadsheet."""

    spreadsheet_id = extract_spreadsheet_id(url_or_id)

    # Safely handle sheet names containing apostrophes.
    safe_sheet_name = sheet_name.replace("'", "''")
    cell_range = f"'{safe_sheet_name}'!A:F"

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_range
    ).execute()

    rows = result.get("values", [])

    if not rows:
        print("The response spreadsheet is empty.")
        return

    headers = [
        str(header).strip().lower()
        for header in rows[0]
    ]

    expected_headers = [
        "timestamp",
        "email address",
        "name",
        "class",
        "reg no",
        "github link"
    ]

    if headers[:6] != expected_headers:
        print("\nHeader validation failed!")
        print("Expected:", expected_headers)
        print("Found:   ", headers)
        return

    submissions = [
        row for row in rows[1:]
        if any(str(cell).strip() for cell in row)
    ]

    print("\nStudent response reading successful!")
    print("Headers verified:", len(headers[:6]), "/ 6")
    print("Total submissions:", len(submissions))
    print("Student data was read but not displayed.")

    return submissions


def read_evaluation_roster(service, url_or_id, sheet_name):
    """Read student roster from columns A:C, starting at row 5."""

    spreadsheet_id = extract_spreadsheet_id(url_or_id)

    safe_sheet_name = sheet_name.replace("'", "''")
    cell_range = f"'{safe_sheet_name}'!A5:C"

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_range
    ).execute()

    return result.get("values", [])



def column_number_to_letter(column_number):
    """Convert a column number into its Google Sheets letter."""
    result = ""

    while column_number:
        column_number, remainder = divmod(column_number - 1, 26)
        result = chr(65 + remainder) + result

    return result



def read_week_link_column(service, url_or_id, sheet_name, week):
    """Read existing values from the weekly GitHub link column."""

    spreadsheet_id = extract_spreadsheet_id(url_or_id)

    if week < 1:
        raise ValueError("Week number must be at least 1.")

    column_number = 4 + (week - 1) * 2
    column_letter = column_number_to_letter(column_number)

    safe_sheet_name = sheet_name.replace("'", "''")
    cell_range = f"'{safe_sheet_name}'!{column_letter}5:{column_letter}1000"

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_range,
        valueRenderOption="FORMATTED_VALUE"
    ).execute()

    values = result.get("values", [])

    # Preserve empty rows so indexes continue matching spreadsheet rows.
    return [
        row if row else [""]
        for row in values
    ]



def write_transfer_plan(service, url_or_id, sheet_name, week, plan):
    """Write GitHub links into verified, empty weekly link cells only."""

    if week < 1:
        raise ValueError("Week number must be at least 1.")

    if not plan:
        print("No links are ready to transfer.")
        return 0

    spreadsheet_id = extract_spreadsheet_id(url_or_id)

    # Calculate the only permitted destination column.
    expected_column = column_number_to_letter(
        4 + (week - 1) * 2
    )

    safe_sheet_name = sheet_name.replace("'", "''")

    ranges = []
    updates = []
    seen_cells = set()

    for item in plan:
        cell = item["cell"]
        link = str(item["github_link"]).strip()

        # Protect score columns and all other columns.
        if not re.fullmatch(
            rf"{expected_column}([5-9]|[1-9]\d+)",
            cell
        ):
            raise ValueError(f"Unsafe destination cell: {cell}")

        if cell in seen_cells:
            raise ValueError(f"Duplicate destination cell: {cell}")

        if not link:
            raise ValueError(f"Empty link in {cell}")

        seen_cells.add(cell)

        ranges.append(f"'{safe_sheet_name}'!{cell}")

        updates.append({
            "range": f"'{safe_sheet_name}'!{cell}",
            "values": [[link]]
        })


    # Write only the individual GitHub link cells.
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "RAW",
            "data": updates
        }
    ).execute()

    updated = result.get("totalUpdatedCells", 0)

    return updated


if __name__ == "__main__":
    try:
        print("Connecting to Google Sheets...")
        sheets_service = get_google_sheets_service()

        print("\nAuthentication successful.")
        spreadsheet_url = input(
            "Paste the URL of one spreadsheet you can access: "
        ).strip()

        test_spreadsheet_connection(sheets_service, spreadsheet_url)
        read_form_responses(sheets_service, spreadsheet_url)

    except HttpError as error:
        print("\nGoogle API error:")
        print(error)

    except Exception as error:
        print(f"\nError: {error}")
