
from google_sheets import read_form_responses
from main import CLASSES, process_class
from week_registry import get_registered_week


def prepare_all_weeks_preview(service, evaluation_url, registered_weeks):

    all_results = []

    for week in registered_weeks:

        week = int(week)

        week_details = get_registered_week(week)

        if not week_details:
            raise ValueError(f"Week {week} is not registered.")

        source_url = week_details["source_url"]

        print(f"Preparing preview for Week {week}...")

        submissions = read_form_responses(service, source_url)

        if not submissions:
            raise ValueError(
                f"No submissions found for Week {week}."
            )

        for class_name in CLASSES.values():

            result = process_class(
                service,
                submissions,
                evaluation_url,
                class_name,
                week
            )

            all_results.append({
                "week": week,
                "class_name": class_name,
                "result": result
            })

    return all_results
