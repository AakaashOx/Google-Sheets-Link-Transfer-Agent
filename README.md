# Google Sheets Link Transfer Agent

A Python + Streamlit application that transfers student GitHub
submission links from Google Form response spreadsheets into a central
evaluation spreadsheet.

The project supports two workflows:

1.  **Weekly transfer** -- register individual weekly response
    spreadsheets, preview a selected week's links, and transfer them to
    the matching evaluation tab.
2.  **Unified transfer** -- read all submissions from one central
    response spreadsheet, identify the task/week from the `Task Number`
    column, retain each student's latest submission for each task, and
    transfer links for one or more weeks.

It also includes an optional scheduled update for a selected registered
week.

> **Important:** The application writes to Google Sheets only after the
> user reviews a preview and explicitly confirms the transfer. Existing
> links in the target week column can be replaced.

------------------------------------------------------------------------

## 1. Features

-   Google Sheets read and write using the Google Sheets API.
-   Student matching by normalized registration number (not fuzzy name
    matching).
-   Separate processing for `BSc AI DS` and `BSc AI ML`.
-   Preview of new links (`INSERT`) and existing links that will be
    overwritten (`REPLACE`).
-   Empty, invalid, unmatched, or ambiguous records are reported rather
    than guessed.
-   Latest-submission selection in Unified Transfer, based on the
    submission timestamp.
-   Unified Transfer modes:
    -   All Weeks
    -   Selected Weeks
    -   Single Week
-   Optional scheduled transfer for one selected registered week.
-   Local logs for scheduled runs.

## 2. Requirements

-   Windows 10/11, macOS, or Linux.
-   Python 3.10 or later.
-   A Google account with access to the source response spreadsheet(s)
    and destination evaluation spreadsheet.
-   Internet access while using the application.
-   A Google Cloud project with the Google Sheets API enabled and OAuth
    credentials configured.

The instructions below use Windows PowerShell. macOS/Linux activation
commands are included where they differ.

------------------------------------------------------------------------

## 3. Download the project

Clone the repository:

``` bash
git clone https://github.com/YOUR-GITHUB-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Alternatively, download the repository as a ZIP file from GitHub,
extract it, and open a terminal in the extracted project folder.

Replace the example GitHub URL above with the actual repository URL.

------------------------------------------------------------------------

## 4. Create a Python virtual environment

### Windows PowerShell

``` powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, run this in the same PowerShell
window and activate again:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

If the `py` command is unavailable, install Python from
https://www.python.org/downloads/ and ensure Python is added to PATH.

### macOS / Linux

``` bash
python3 -m venv venv
source venv/bin/activate
```

------------------------------------------------------------------------

## 5. Install the dependencies

With the virtual environment activated, run:

``` bash
python -m pip install --upgrade pip
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pandas streamlit python-dotenv
```

If the repository includes a `requirements.txt`, use this instead:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 6. Configure Google Sheets API access

Each person who runs the application must configure their own Google API
credentials. **Do not use another person's `credentials.json` or
`token.json`.**

### A. Create or select a Google Cloud project

1.  Open the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project or select an existing project.
3.  Open **APIs & Services → Library**.
4.  Search for **Google Sheets API**.
5.  Open it and click **Enable**.

### B. Configure the OAuth consent screen

1.  Open **APIs & Services → OAuth consent screen**.
2.  Complete the required application details.
3.  If the app is in testing mode, add the Google account that will run
    the application as a test user.
4.  Save the configuration.

Google may change the names or layout of these screens. Follow the
current Google Cloud Console prompts.

### C. Create an OAuth Desktop application credential

1.  Open **APIs & Services → Credentials**.
2.  Choose **Create Credentials → OAuth client ID**.
3.  Select **Desktop app** as the application type.
4.  Create the credential.
5.  Download the JSON file.

Create a folder named `credentials` in the project root and place the
downloaded file there, renaming it to:

``` text
credentials/credentials.json
```

The project expects this exact location and filename.

### D. First authorization

When the application first connects to Google Sheets, Google will ask
the user to authorize access. Complete the browser sign-in using the
Google account that has access to the spreadsheets.

The application will create:

``` text
credentials/token.json
```

This token is used for later connections. Keep both credential files
private. Do not upload them to GitHub, email them to other users, or
share them publicly.

If authorization needs to be reset, close the application, remove your
local `credentials/token.json`, and run the application again to
authorize.

------------------------------------------------------------------------

## 7. Give the authorized Google account spreadsheet access

The Google account used in the OAuth browser sign-in must have the
necessary permissions:

-   **Source response spreadsheet(s):** Viewer access is sufficient.
-   **Destination evaluation spreadsheet:** Editor access is required
    because the application writes GitHub links.

If a spreadsheet belongs to another person or organization, ask its
owner to share it with the Google account you use to authorize the
application.

The application does not bypass Google Drive or spreadsheet permissions.

------------------------------------------------------------------------

## 8. Spreadsheet formats

### A. Destination evaluation spreadsheet

The destination spreadsheet must contain these worksheet tabs:

-   `BSc AI DS`
-   `BSc AI ML`

The expected layout is:

  Column   Content
  -------- ---------------------------------------------
  A        Serial number
  B        Registration number
  C        Student name
  D        Week 1 GitHub link
  E        Week 1 score
  F        Week 2 GitHub link
  G        Week 2 score
  H        Week 3 GitHub link
  I        Week 3 score
  ...      Continue alternating link and score columns

Student records start at **row 5**.

The application writes only to the relevant week's link column:

-   Week 1 → D
-   Week 2 → F
-   Week 3 → H
-   Week 4 → J
-   and so on.

Score columns, student details, headings, and formatting are not
intended to be modified.

Registration numbers must uniquely identify students in the relevant
evaluation tab. If the same registration number appears more than once,
the application flags it rather than choosing a row automatically.

### B. Weekly Transfer source spreadsheet

For the original Weekly Transfer workflow, each registered weekly source
spreadsheet should contain the expected response columns:

-   Timestamp
-   Email Address
-   Name
-   Class
-   Reg No
-   GitHub Link

The source is read from the response worksheet. Register the source
spreadsheet URL and the destination evaluation spreadsheet URL in the
dashboard.

### C. Unified Transfer central spreadsheet

Unified Transfer uses one central response spreadsheet. Its first
worksheet tab must contain these columns (header capitalization and
surrounding spaces are normalized):

-   `Timestamp`
-   `Email Address`
-   `Name`
-   `Class`
-   `Reg No`
-   `Task Number`
-   `Github Link`

The `Task Number` should contain a week/task number, for example
`Task 1`, `Task 2`, ... `Task 12`. The extracted number determines the
destination week.

The class value should identify the relevant class, such as
`III BSc AI ML` or `III BSc AI DS`. These are mapped to the destination
tabs `BSc AI ML` and `BSc AI DS`.

If a student submits more than once for the same task, the application
retains the latest valid submission based on the timestamp. Records with
invalid timestamps, missing required values, unrecognized classes, or
conflicting latest submissions are reported and should be resolved
before writing.

**Timestamp note:** Make sure the source spreadsheet's timestamp values
are consistent and unambiguous. If your spreadsheet uses a different
date format, check the timestamp parser in `unified_matcher.py` before
processing real submissions.

------------------------------------------------------------------------

## 9. Run the Streamlit dashboard

From the project root, with the virtual environment activated:

``` bash
streamlit run dashboard.py
```

Streamlit will show a local URL in the terminal, usually:

``` text
http://localhost:8501
```

Open that address in your browser.

### Weekly Transfer

1.  Register a week with its source response spreadsheet URL and
    evaluation spreadsheet URL.
2.  Select the registered week.
3.  Generate the preview.
4.  Review matched students, unmatched students, skipped records, and
    `INSERT` / `REPLACE` actions.
5.  Confirm the transfer only after checking the preview.
6.  Use **Update All Registered Weeks** only when you intentionally want
    to process every registered week.

### Unified Transfer

1.  Enter the central responses spreadsheet URL.
2.  Enter the evaluation spreadsheet URL.
3.  Choose **All Weeks**, **Selected Weeks**, or **Single Week**.
4.  Generate the preview.
5.  Review the counts and transfer actions for every displayed week and
    class.
6.  Tick the confirmation checkbox and click the write button only when
    the preview is correct.

Do not assume that every source submission will be transferred. Check
unmatched and skipped records in the preview. Resolve unexpected records
before confirming.

------------------------------------------------------------------------

## 10. Optional scheduled automation (Windows)

The project includes an optional scheduled runner for a selected
registered week.

The dashboard lets the user select a registered week and enable, pause,
resume, or disable automation. The scheduled runner checks the local
automation settings before it accesses Google Sheets.

To configure Windows Task Scheduler:

1.  Open **Task Scheduler**.

2.  Create a task with a weekly trigger at the required day and time.

3.  Set **Program/script** to the virtual environment's Python
    executable:

    ``` text
    YOUR-PROJECT-FOLDER\venv\Scripts\python.exe
    ```

4.  Set **Add arguments** to:

    ``` text
    scheduled_runner.py
    ```

5.  Set **Start in** to the full project root folder.

6.  Save the task.

7.  Enable automation and select the intended week in the dashboard.

The laptop/computer must be awake, connected to the internet, and able
to access Google Sheets when the task runs. The local project folder and
virtual environment must remain in place.

Scheduled automation can write links and replace existing links for the
selected week. Enable it only after checking the selected week and
understanding the overwrite behavior. Review:

``` text
logs/automation.log
```

for scheduled-run records.

Task Scheduler setup is optional. The dashboard's manual transfer
workflows do not require it.

------------------------------------------------------------------------

## 11. Important local files

  -----------------------------------------------------------------------
  Path                                Purpose
  ----------------------------------- -----------------------------------
  `dashboard.py`                      Streamlit user interface

  `main.py`                           Core weekly processing workflow

  `google_sheets.py`                  Google Sheets authentication and
                                      read/write functions

  `student_matcher.py`                Registration-number matching

  `link_transfer.py`                  Prepares link transfer plans

  `week_registry.py`                  Stores locally registered weeks

  `bulk_transfer.py`                  Prepares previews for all
                                      registered weeks

  `unified_transfer.py`               Reads the central response
                                      spreadsheet

  `unified_matcher.py`                Parses tasks, normalizes classes,
                                      and selects latest submissions

  `unified_preview.py`                Prepares previews for selected
                                      unified weeks

  `automation_registry.py`            Stores local automation settings

  `scheduled_runner.py`               Runs the selected scheduled
                                      transfer

  `logs/automation.log`               Scheduled automation log
  -----------------------------------------------------------------------

Local settings and credentials are created on the computer running the
project. They are not automatically shared when another person clones
the GitHub repository.

------------------------------------------------------------------------

## 12. Security: files that must not be uploaded to GitHub

Never commit or publish:

-   `credentials/credentials.json`
-   `credentials/token.json`
-   Any Google OAuth client secret or access token
-   Private spreadsheet URLs if they are not intended to be public
-   Student names, registration numbers, email addresses, or submission
    data
-   Local logs containing sensitive information

The repository should include a `.gitignore` that excludes credentials,
virtual environments, tokens, local configuration, and logs.

Before pushing to GitHub, inspect the files being committed. If a
credential or token has already been pushed, deleting it in a later
commit is not enough: revoke/rotate the exposed credential in Google
Cloud Console and remove the secret from the repository history as
appropriate.

------------------------------------------------------------------------

## 13. Troubleshooting

### `credentials/credentials.json` not found

Create the `credentials` folder and place your downloaded Google OAuth
Desktop app JSON file inside it with the exact name `credentials.json`.

### Google asks for authorization again

Complete the browser authorization. If the local token is invalid, close
the app, delete your own `credentials/token.json`, and authorize again.

### `403` or permission errors from Google Sheets

Check that Google Sheets API is enabled and that the Google account used
for OAuth has access to the source and destination spreadsheets. The
destination account needs Editor access.

### Student is unmatched

Check the registration number in the source and destination evaluation
tab. The application uses registration-number matching; it does not
guess a student based on a similar name.

### Duplicate registration number in the evaluation roster

Correct the duplicate in the destination evaluation sheet before
transferring. The application should not choose between multiple
destination rows automatically.

### Streamlit cannot start

Make sure the virtual environment is activated and dependencies are
installed. Run:

``` bash
python -m pip install -r requirements.txt
```

If there is no `requirements.txt`, use the installation command in
Section 5.

### Windows Application Control blocks a Pandas `.pyd` file

Some managed Windows devices block compiled Python package files. The
dashboard avoids Pandas-based table rendering in affected sections, but
a device policy may still block a dependency imported elsewhere. Follow
your organization's IT/security process rather than downloading
replacement `.pyd` files from untrusted websites.

------------------------------------------------------------------------

## 14. Before using it with real student data

-   Test with a copy of the evaluation spreadsheet first.
-   Confirm the source and destination spreadsheet URLs.
-   Confirm the class and registration-number columns.
-   Review every preview before writing.
-   Check `REPLACE` actions carefully because they overwrite existing
    links.
-   Keep OAuth credentials and student information private.
-   Do not run a scheduled task manually while automation is enabled
    unless you intend to trigger an immediate transfer.

------------------------------------------------------------------------

