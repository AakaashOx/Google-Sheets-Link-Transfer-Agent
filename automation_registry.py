
import json
from pathlib import Path

CONFIG_FILE = Path("config/automation_settings.json")


def load_automation_settings():

    if not CONFIG_FILE.exists():
        return {
            "selected_week": None,
            "enabled": False,
            "paused": False,
            "schedule_day": "Friday",
            "schedule_time": "15:00",
            "timezone": "Asia/Kolkata"
        }

    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


def save_automation_settings(settings):

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w") as file:
        json.dump(settings, file, indent=4)


def configure_automation(week):

    settings = load_automation_settings()

    settings["selected_week"] = int(week)
    settings["schedule_day"] = "Friday"
    settings["schedule_time"] = "15:00"
    settings["timezone"] = "Asia/Kolkata"

    # Require explicit activation after selecting a week
    settings["enabled"] = False
    settings["paused"] = False

    save_automation_settings(settings)


def enable_automation():

    settings = load_automation_settings()

    if settings["selected_week"] is None:
        raise ValueError("Select a week before enabling automation.")

    settings["enabled"] = True
    settings["paused"] = False

    save_automation_settings(settings)


def pause_automation():

    settings = load_automation_settings()

    settings["paused"] = True

    save_automation_settings(settings)


def resume_automation():

    settings = load_automation_settings()

    if settings["selected_week"] is None:
        raise ValueError("No week is selected for automation.")

    settings["enabled"] = True
    settings["paused"] = False

    save_automation_settings(settings)


def disable_automation():

    settings = load_automation_settings()

    settings["enabled"] = False
    settings["paused"] = False

    save_automation_settings(settings)


def get_automation_status():

    settings = load_automation_settings()

    if not settings["enabled"]:
        status = "DISABLED"
    elif settings["paused"]:
        status = "PAUSED"
    else:
        status = "ACTIVE"

    return status



def clear_automation_selection():

    settings = load_automation_settings()

    if settings["enabled"]:
        raise ValueError(
            "Disable automation before clearing its selected week."
        )

    settings["selected_week"] = None
    settings["paused"] = False

    save_automation_settings(settings)
