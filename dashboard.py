
from week_registry import unregister_week

from automation_registry import (
    load_automation_settings,
    configure_automation,
    enable_automation,
    pause_automation,
    resume_automation,
    disable_automation,
    clear_automation_selection,
    get_automation_status
)


from week_registry import (
    load_registry,
    register_week,
    get_registered_weeks,
    get_registered_week
)

import streamlit as st

from bulk_transfer import prepare_all_weeks_preview

from google_sheets import (
    get_google_sheets_service,
    read_form_responses,
    write_transfer_plan
)

from main import CLASSES, process_class

from unified_transfer import read_unified_responses

from unified_matcher import prepare_unified_submissions

from unified_preview import prepare_unified_preview


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Google Sheets Transfer Agent",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(
            135deg,
            #F8FBFF 0%,
            #EEF4FF 48%,
            #FFFFFF 100%
        );
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        color: #172B4D;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 42px;
    }

    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
    }

    input, textarea {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


st.title("📊 Google Sheets Transfer Agent")
st.caption("Weekly GitHub submission management")

# Store preview between Streamlit reruns
if "preview_data" not in st.session_state:
    st.session_state.preview_data = None


# ---------------- INPUT SECTION ----------------


# ---------------- WEEK REGISTRATION & SELECTION ----------------

registry = load_registry()

st.header("1. Weekly Management")

register_tab, update_tab = st.tabs([
    "➕ Register New Week",
    "📂 Update Selected Week"
])

# REGISTER NEW WEEK
with register_tab:

    st.subheader("Register a weekly Form Responses sheet")

    saved_evaluation_url = registry.get("evaluation_url", "")

    with st.form("register_week_form"):

        new_week = st.number_input(
            "Week Number",
            min_value=1,
            max_value=30,
            value=1,
            step=1,
            key="new_week_number"
        )

        new_source_url = st.text_input(
            "Weekly Form Responses Spreadsheet URL",
            placeholder="Paste the new weekly response URL"
        )

        new_evaluation_url = st.text_input(
            "Evaluation Spreadsheet URL",
            value=saved_evaluation_url,
            placeholder="Paste your evaluation spreadsheet URL"
        )

        register_submitted = st.form_submit_button(
            "Register Week",
            type="primary"
        )

        if register_submitted:

            try:
                register_week(
                    int(new_week),
                    new_source_url,
                    new_evaluation_url
                )

                st.success(f"Week {int(new_week)} registered successfully!")
                st.rerun()

            except Exception as error:
                st.error(f"Registration failed: {error}")


# UPDATE SELECTED WEEK
with update_tab:

    st.subheader("Choose a registered week")

    registered_weeks = get_registered_weeks()

    if registered_weeks:

        selected_week = st.selectbox(
            "Select Week",
            options=registered_weeks,
            format_func=lambda value: f"Week {value}"
        )

        week = int(selected_week)

        week_details = get_registered_week(week)

        source_url = week_details["source_url"]
        evaluation_url = registry["evaluation_url"]

        st.success(f"Week {week} is registered and ready.")

        st.caption(
            f"Registered on: {week_details.get('registered_at', 'Unknown')}"
        )

    else:

        selected_week = None
        week = 1
        source_url = ""
        evaluation_url = ""

        st.info(
            "No weeks have been registered yet. "
            "Register your first week using the Register New Week tab."
        )


signature = (
    source_url.strip(),
    evaluation_url.strip(),
    int(week)
)


# ---------------- PREVIEW TRANSFERS ----------------

st.divider()
st.header("2. Preview Transfers")

if st.button("🔍 Generate Transfer Preview", type="primary"):

    if selected_week is None:
        st.error("Please register a week before generating a preview.")

    elif not source_url.strip() or not evaluation_url.strip():
        st.error("Please register both spreadsheet URLs.")

    else:
        try:
            with st.spinner("Reading spreadsheets and matching students..."):

                service = get_google_sheets_service()

                submissions = read_form_responses(
                    service,
                    source_url.strip()
                )

                if submissions is None:
                    st.error("Invalid source spreadsheet.")
                    st.stop()

                all_class_data = []

                for class_name in CLASSES.values():

                    class_data = process_class(
                        service,
                        submissions,
                        evaluation_url.strip(),
                        class_name,
                        int(week)
                    )

                    all_class_data.append(class_data)

                st.session_state.preview_data = {
                    "signature": signature,
                    "classes": all_class_data
                }

                # Clear any previous transfer report
                st.session_state.pop("transfer_report", None)

            st.success(
                f"Week {week} preview generated successfully!"
            )

        except Exception as error:
            st.error(f"Preview failed: {error}")



# ---------------- DISPLAY PREVIEW ----------------

preview = st.session_state.preview_data

if preview is not None and preview["signature"] == signature:

    st.divider()
    st.header("3. Transfer Summary")

    total_links = sum(
        len(item["transfer"]["plan"])
        for item in preview["classes"]
    )

    total_skipped = sum(
        len(item["transfer"]["skipped"])
        for item in preview["classes"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Week", week)
    col2.metric("Links Ready", total_links)
    col3.metric("Skipped", total_skipped)

    for class_data in preview["classes"]:

        class_name = class_data["class_name"]
        results = class_data["results"]
        transfer = class_data["transfer"]

        with st.expander(
            f"{class_name} — {len(transfer['plan'])} links ready",
            expanded=True
        ):

            st.write("**Matching Summary**")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Matched", len(results["matched"]))
            col2.metric("Unmatched", len(results["unmatched"]))
            col3.metric(
                "Duplicate Submissions",
                len(results["duplicate_submissions"])
            )
            col4.metric(
                "Duplicate Roster",
                len(results["duplicate_roster"])
            )

            st.write("**Destination Cells**")

            if transfer["plan"]:

                display_rows = [
                    {
                        "Registration Number": item["reg_no"],
                        "Destination Cell": item["cell"],
                        "Action": item["action"]
                    }
                    for item in transfer["plan"]
                ]

                table = "| Registration Number | Destination Cell | Action |\n"
                table += "|---|---|---|\n"

                for item in display_rows:
                    table += (
                        f"| {item['Registration Number']} "
                        f"| {item['Destination Cell']} "
                        f"| {item['Action']} |\n"
                    )

                st.markdown(table)

            else:
                st.info("No links ready for transfer.")

            if transfer["skipped"]:

                st.write("**Skipped Records**")

                skipped_rows = [
                    {
                        "Registration Number": item["reg_no"],
                        "Reason": item["reason"]
                    }
                    for item in transfer["skipped"]
                ]

                table = "| Registration Number | Reason |\n"
                table += "|---|---|\n"

                for item in skipped_rows:
                    table += (
                        f"| {item['Registration Number']} "
                        f"| {item['Reason']} |\n"
                    )

                st.markdown(table)

            if results["unmatched"]:
                with st.expander("View unmatched submissions"):
                    st.json(results["unmatched"])

            if results["duplicate_submissions"]:
                st.write("Duplicate submissions:")
                st.code(str(results["duplicate_submissions"]))

            if results["duplicate_roster"]:
                st.write("Duplicate roster entries:")
                st.code(str(results["duplicate_roster"]))


    # ---------------- WRITE CONFIRMATION ----------------

    st.divider()
    st.header("4. Confirm Transfer")

    st.warning(
        "This action will write GitHub links into the selected "
        "week's link columns in both class tabs. Existing links "
        "marked REPLACE will be overwritten."
    )

    confirm = st.checkbox(
        f"I have reviewed the Week {week} transfer preview "
        "and authorize these spreadsheet changes."
    )

    if st.button(
        "✅ Confirm and Transfer Links",
        type="primary",
        disabled=not confirm or total_links == 0
    ):

        try:
            service = get_google_sheets_service()

            report = []

            progress = st.progress(0)

            for index, class_data in enumerate(preview["classes"]):

                class_name = class_data["class_name"]
                transfer = class_data["transfer"]

                plan = transfer["plan"]

                if not plan:
                    report.append({
                        "class": class_name,
                        "inserted": 0,
                        "replaced": 0,
                        "updated": 0,
                        "failed": 0,
                        "status": "No links to transfer"
                    })

                    progress.progress((index + 1) / len(preview["classes"]))
                    continue

                try:
                    updated = write_transfer_plan(
                        service,
                        evaluation_url.strip(),
                        class_name,
                        int(week),
                        plan
                    )

                    inserted = sum(
                        1 for item in plan
                        if item["action"] == "INSERT"
                    )

                    replaced = sum(
                        1 for item in plan
                        if item["action"] == "REPLACE"
                    )

                    failed = max(0, len(plan) - updated)

                    report.append({
                        "class": class_name,
                        "inserted": inserted,
                        "replaced": replaced,
                        "updated": updated,
                        "failed": failed,
                        "status": "Completed" if failed == 0 else "Check results"
                    })

                except Exception as error:

                    report.append({
                        "class": class_name,
                        "inserted": 0,
                        "replaced": 0,
                        "updated": 0,
                        "failed": len(plan),
                        "status": str(error)
                    })

                progress.progress((index + 1) / len(preview["classes"]))

            st.session_state.transfer_report = report
            st.session_state.preview_data = None

            st.success("Transfer process finished.")

        except Exception as error:
            st.error(f"Transfer process failed: {error}")


# ---------------- TRANSFER REPORT ----------------

if "transfer_report" in st.session_state:

    st.divider()
    st.header("5. Transfer Report")

    for item in st.session_state.transfer_report:

        st.subheader(item["class"])

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Inserted", item["inserted"])
        col2.metric("Replaced", item["replaced"])
        col3.metric("Updated", item["updated"])
        col4.metric("Failed", item["failed"])

        if item["failed"] == 0:
            st.success(item["status"])
        else:
            st.error(item["status"])


# ==========================================
# UPDATE ALL REGISTERED WEEKS
# ==========================================

st.divider()
st.header("3. Update All Registered Weeks")

registered_weeks = get_registered_weeks()
registry_data = load_registry()

bulk_evaluation_url = registry_data.get("evaluation_url", "")

bulk_signature = (
    tuple(int(w) for w in registered_weeks),
    bulk_evaluation_url
)

# Initialise separate bulk preview storage
if "bulk_preview_data" not in st.session_state:
    st.session_state.bulk_preview_data = None

if "bulk_preview_signature" not in st.session_state:
    st.session_state.bulk_preview_signature = None

if "bulk_write_report" not in st.session_state:
    st.session_state.bulk_write_report = None


if not registered_weeks:

    st.info("No registered weeks available.")

else:

    st.write(
        f"Registered weeks: {', '.join(str(w) for w in registered_weeks)}"
    )

    st.warning(
        "This option prepares updates for every registered week "
        "and both classes. Review the complete preview before confirming."
    )

    if st.button(
        "Prepare Update All Preview",
        type="secondary"
    ):

        try:

            service = get_google_sheets_service()

            with st.spinner("Preparing previews for all registered weeks..."):

                preview = prepare_all_weeks_preview(
                    service,
                    bulk_evaluation_url,
                    registered_weeks
                )

            st.session_state.bulk_preview_data = preview
            st.session_state.bulk_preview_signature = bulk_signature
            st.session_state.bulk_write_report = None
            st.session_state.bulk_confirm_checkbox = False

            st.success("All weekly previews prepared successfully.")

        except Exception as error:

            st.session_state.bulk_preview_data = None
            st.session_state.bulk_preview_signature = None

            st.error(f"Could not prepare bulk preview: {error}")


    bulk_preview = st.session_state.bulk_preview_data

    if bulk_preview:

        if st.session_state.bulk_preview_signature != bulk_signature:

            st.warning(
                "The registered weeks have changed. "
                "Prepare the bulk preview again before continuing."
            )

            st.session_state.bulk_preview_data = None

        else:

            st.subheader("Combined Transfer Preview")

            total_links = 0

            for item in bulk_preview:

                week = item["week"]
                class_name = item["class_name"]
                result = item["result"]
                transfer = result["transfer"]

                plan = transfer["plan"]
                skipped = transfer["skipped"]

                total_links += len(plan)

                with st.expander(
                    f"Week {week} — {class_name} "
                    f"({len(plan)} links)"
                ):

                    st.write("Transfer actions:")

                                        
                    if plan:

                        # Build a readable table using the actual transfer-plan fields
                        columns = list(plan[0].keys())

                        header = "| " + " | ".join(columns) + " |"
                        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

                        rows = []

                        for entry in plan:

                            values = [
                                str(entry.get(column, "")).replace("|", "\\|").replace("\n", " ")
                                for column in columns
                            ]

                            rows.append("| " + " | ".join(values) + " |")

                        table = "\n".join([header, separator] + rows)

                        st.markdown(table)

                    else:
                        st.info("No links to transfer for this class.")


                    if skipped:
                        st.write("Skipped submissions:")
                        st.json(skipped)

            st.metric("Total links prepared", total_links)

            st.checkbox(
                "I have reviewed the previews for all weeks and classes.",
                key="bulk_confirm_checkbox"
            )

            if st.button(
                "Confirm Update All Registered Weeks",
                type="primary",
                disabled=not st.session_state.bulk_confirm_checkbox
            ):

                service = get_google_sheets_service()

                report = []

                progress = st.progress(0)
                status = st.empty()

                total_items = len(bulk_preview)

                for index, item in enumerate(bulk_preview):

                    week = item["week"]
                    class_name = item["class_name"]
                    plan = item["result"]["transfer"]["plan"]

                    status.write(
                        f"Updating Week {week} — {class_name}..."
                    )

                    try:

                        if plan:

                            updated = write_transfer_plan(
                                service,
                                bulk_evaluation_url,
                                class_name,
                                week,
                                plan
                            )

                        else:

                            updated = 0

                        report.append({
                            "week": week,
                            "class_name": class_name,
                            "updated": updated,
                            "status": "SUCCESS"
                        })

                    except Exception as error:

                        report.append({
                            "week": week,
                            "class_name": class_name,
                            "updated": 0,
                            "status": "FAILED",
                            "error": str(error)
                        })

                    progress.progress((index + 1) / total_items)

                st.session_state.bulk_write_report = report
                st.session_state.bulk_preview_data = None
                st.session_state.bulk_preview_signature = None

                status.empty()
                progress.empty()

                st.rerun()


# Display the latest bulk update report

if st.session_state.bulk_write_report:

    st.subheader("Update All — Transfer Report")

    successful = sum(
        1 for item in st.session_state.bulk_write_report
        if item["status"] == "SUCCESS"
    )

    failed = sum(
        1 for item in st.session_state.bulk_write_report
        if item["status"] == "FAILED"
    )

    st.write(f"Successful class updates: {successful}")
    st.write(f"Failed class updates: {failed}")

    for item in st.session_state.bulk_write_report:

        if item["status"] == "SUCCESS":

            st.success(
                f"Week {item['week']} — {item['class_name']}: "
                f"{item['updated']} links updated."
            )

        else:

            st.error(
                f"Week {item['week']} — {item['class_name']}: "
                f"{item['error']}"
            )


# ==========================================
# AUTOMATION & WEEK MANAGEMENT
# ==========================================

st.divider()
st.header("4. Automation & Week Management")

registered_weeks = [int(w) for w in get_registered_weeks()]
automation_settings = load_automation_settings()

selected_automation_week = automation_settings.get("selected_week")
automation_status = get_automation_status()

# ------------------------------------------
# AUTOMATION CONFIGURATION
# ------------------------------------------

st.subheader("Scheduled Automation")

st.write("Configure automatic updates for one registered week.")

if registered_weeks:

    default_index = 0

    if selected_automation_week in registered_weeks:
        default_index = registered_weeks.index(
            selected_automation_week
        )

    week_to_schedule = st.selectbox(
        "Select the week for automatic updates",
        options=registered_weeks,
        index=default_index,
        format_func=lambda w: f"Week {w}",
        key="automation_week_selector"
    )

    st.caption("Schedule: Every Friday at 3:00 PM IST")

    if st.button("Save Selected Automation Week"):

        try:
            configure_automation(week_to_schedule)

            st.success(
                f"Week {week_to_schedule} selected. "
                "Enable automation when ready."
            )

            st.rerun()

        except Exception as error:
            st.error(str(error))

else:
    st.info("Register a week before configuring automation.")


# ------------------------------------------
# AUTOMATION STATUS
# ------------------------------------------

automation_settings = load_automation_settings()
automation_status = get_automation_status()
selected_automation_week = automation_settings.get("selected_week")

st.subheader("Automation Status")

st.write(
    f"Selected week: "
    f"{'Week ' + str(selected_automation_week) if selected_automation_week else 'None'}"
)

st.write("Schedule: Friday, 3:00 PM IST")

if automation_status == "ACTIVE":
    st.success("Automation is enabled and not paused.")

elif automation_status == "PAUSED":
    st.warning("Automation is paused.")

else:
    st.info("Automation is disabled.")


# ------------------------------------------
# AUTOMATION CONTROLS
# ------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:

    if st.button(
        "Enable Automation",
        disabled=(
            selected_automation_week is None
            or automation_status == "ACTIVE"
        )
    ):

        try:
            enable_automation()
            st.success("Automation enabled.")
            st.rerun()

        except Exception as error:
            st.error(str(error))


with col2:

    if st.button(
        "Pause Automation",
        disabled=(automation_status != "ACTIVE")
    ):

        pause_automation()
        st.warning("Automation paused.")
        st.rerun()


with col3:

    if st.button(
        "Resume Automation",
        disabled=(automation_status != "PAUSED")
    ):

        try:
            resume_automation()
            st.success("Automation resumed.")
            st.rerun()

        except Exception as error:
            st.error(str(error))


if st.button(
    "Disable Automation",
    disabled=(automation_status == "DISABLED")
):

    disable_automation()
    st.info("Automation disabled. Your selected week is retained.")
    st.rerun()


if st.button(
    "Clear Selected Automation Week",
    disabled=(
        selected_automation_week is None
        or automation_settings.get("enabled", False)
    )
):

    try:
        clear_automation_selection()
        st.success("Automation week selection cleared.")
        st.rerun()

    except Exception as error:
        st.error(str(error))


# ------------------------------------------
# UNREGISTER A WEEK
# ------------------------------------------

st.divider()
st.subheader("Unregister a Week")

st.caption(
    "This removes a week from your local registry only. "
    "It does not delete Google Sheets or their contents."
)

if registered_weeks:

    week_to_remove = st.selectbox(
        "Choose a week to unregister",
        options=registered_weeks,
        format_func=lambda w: f"Week {w}",
        key="unregister_week_selector"
    )

    confirm_unregister = st.checkbox(
        f"I confirm that I want to unregister Week {week_to_remove}.",
        key="confirm_unregister_week"
    )

    if st.button(
        "Unregister Selected Week",
        type="secondary",
        disabled=not confirm_unregister
    ):

        try:
            unregister_week(week_to_remove)

            st.success(f"Week {week_to_remove} unregistered.")
            st.rerun()

        except Exception as error:
            st.error(str(error))

else:
    st.info("There are no registered weeks to unregister.")



# ------------------------------------------
# UNIFIED ALL-WEEKS TRANSFER
# ------------------------------------------

st.divider()
st.header("Unified All-Weeks Transfer")

st.caption(
    "Read submissions from one central Google Sheet "
    "and transfer GitHub links to the corresponding evaluation weeks."
)

unified_source_url = st.text_input(
    "Central Responses Spreadsheet URL",
    key="unified_source_url"
)

unified_evaluation_url = st.text_input(
    "Evaluation Spreadsheet URL",
    key="unified_evaluation_url"
)

unified_mode = st.radio(
    "Choose Update Mode",
    [
        "All Weeks",
        "Selected Weeks",
        "Single Week"
    ],
    key="unified_update_mode"
)

selected_unified_weeks = []

if unified_mode == "Selected Weeks":
    selected_unified_weeks = st.multiselect(
        "Choose Weeks",
        options=list(range(1, 13)),
        format_func=lambda w: f"Week {w}",
        key="unified_selected_weeks"
    )

elif unified_mode == "Single Week":
    single_unified_week = st.selectbox(
        "Choose Week",
        options=list(range(1, 13)),
        format_func=lambda w: f"Week {w}",
        key="unified_single_week"
    )

if st.button(
    "Generate Unified Transfer Preview",
    type="primary",
    key="generate_unified_preview"
):
    if not unified_source_url.strip() or not unified_evaluation_url.strip():
        st.error("Please enter both spreadsheet URLs.")

    elif (
        unified_mode == "Selected Weeks"
        and not selected_unified_weeks
    ):
        st.error("Please select at least one week.")

    else:
        try:
            service = get_google_sheets_service()

            with st.spinner("Reading central responses..."):
                submissions = read_unified_responses(
                    service,
                    unified_source_url
                )

                prepared, skipped, duplicates, conflicts = (
                    prepare_unified_submissions(submissions)
                )

            st.write("Total submissions:", len(submissions))
            st.write("Latest submissions retained:", len(prepared))
            st.write("Older submissions discarded:", duplicates)

            if skipped or conflicts:
                st.error(
                    "Data issues were detected. "
                    "Please resolve them before transferring."
                )
                st.write("Skipped records:", skipped)
                st.write("Timestamp conflicts:", conflicts)

            else:
                if unified_mode == "All Weeks":
                    weeks_to_process = None

                elif unified_mode == "Selected Weeks":
                    weeks_to_process = selected_unified_weeks

                else:
                    weeks_to_process = [single_unified_week]

                with st.spinner("Preparing transfer preview..."):
                    preview = prepare_unified_preview(
                        service,
                        unified_evaluation_url,
                        prepared,
                        weeks_to_process
                    )

                st.session_state["unified_preview"] = preview
                st.session_state["unified_service_ready"] = True
                st.session_state["unified_eval_url_for_write"] = unified_evaluation_url

                st.success("Unified transfer preview generated.")

        except Exception as error:
            st.error(f"Preview failed: {error}")



# ------------------------------------------
# UNIFIED TRANSFER PREVIEW AND WRITE
# ------------------------------------------

if "unified_preview" in st.session_state:

    preview = st.session_state["unified_preview"]

    st.divider()
    st.subheader("Unified Transfer Preview")

    st.write(
        "Weeks selected:",
        ", ".join(
            f"Week {week}"
            for week in preview["selected_weeks"]
        )
    )

    total_planned = 0

    for entry in preview["results"]:

        week = entry["week"]
        class_name = entry["class_name"]
        result = entry["result"]

        transfer = result["transfer"]
        plan = transfer["plan"]
        skipped_records = transfer["skipped"]
        matching = result["results"]

        total_planned += len(plan)

        with st.expander(
            f"Week {week} - {class_name} "
            f"({len(plan)} planned updates)",
            expanded=True
        ):

            st.write(
                "Matched students:",
                len(matching["matched"])
            )

            st.write(
                "Unmatched students:",
                len(matching["unmatched"])
            )

            st.write(
                "Planned updates:",
                len(plan)
            )

            st.write(
                "Skipped transfers:",
                len(skipped_records)
            )

            if plan:
                st.markdown("**Transfer actions**")

                for item in plan:
                    st.write(
                        f'{item["reg_no"]} — {item["action"]}'
                    )

            if matching["unmatched"]:
                st.warning("Some students could not be matched.")
                st.json(matching["unmatched"])

            if skipped_records:
                st.warning("Some transfers were skipped.")
                st.json(skipped_records)

    st.subheader("Transfer Summary")
    st.write("Total planned updates:", total_planned)

    st.warning(
        "Confirm only after checking the preview. "
        "Existing links marked REPLACE will be overwritten."
    )

    confirm_unified_write = st.checkbox(
        "I have reviewed the preview and confirm these updates.",
        key="confirm_unified_write"
    )

    if st.button(
        "Write Unified Transfer to Google Sheets",
        type="primary",
        disabled=(
            not confirm_unified_write
            or total_planned == 0
        ),
        key="write_unified_transfer"
    ):

        try:
            service = get_google_sheets_service()

            successful_updates = 0

            for entry in preview["results"]:

                plan = entry["result"]["transfer"]["plan"]

                if not plan:
                    continue

                updated = write_transfer_plan(
                    service,
                    st.session_state["unified_eval_url_for_write"],
                    entry["class_name"],
                    entry["week"],
                    plan
                )

                successful_updates += updated

                st.write(
                    f'Week {entry["week"]} - '
                    f'{entry["class_name"]}: '
                    f'{updated} cells updated.'
                )

            st.success(
                f"Unified transfer completed. "
                f"{successful_updates} cells updated."
            )

            del st.session_state["unified_preview"]
            st.session_state.pop("unified_eval_url_for_write", None)
            st.session_state.pop("confirm_unified_write", None)

        except Exception as error:
            st.error(f"Transfer failed: {error}")
