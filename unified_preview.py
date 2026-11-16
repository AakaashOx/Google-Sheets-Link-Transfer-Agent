
from main import CLASSES, process_class


def prepare_unified_preview(
    service,
    evaluation_url,
    prepared_submissions,
    selected_weeks=None
):
    """
    Prepare transfer previews for all or selected weeks.

    selected_weeks:
        None = all detected weeks
        [1, 3, 5] = only selected weeks
    """

    available_weeks = sorted({
        item["week"]
        for item in prepared_submissions
    })

    if selected_weeks is None:
        weeks_to_process = available_weeks
    else:
        weeks_to_process = sorted({
            int(week) for week in selected_weeks
        })

    invalid_weeks = [
        week for week in weeks_to_process
        if week not in available_weeks
    ]

    if invalid_weeks:
        raise ValueError(
            f"No submissions found for weeks: {invalid_weeks}"
        )

    all_results = []

    for week in weeks_to_process:

        for class_name in CLASSES.values():

            # Filter submissions for this week and class
            week_submissions = [
                item for item in prepared_submissions
                if item["week"] == week
                and item["class_name"] == class_name
            ]

            if not week_submissions:
                continue

            # Convert to the six-column row format expected
            # by the existing student matcher.
            compatible_submissions = []

            for item in week_submissions:
                compatible_submissions.append([
                    item["original_timestamp"],
                    item["email"],
                    item["name"],
                    class_name,
                    item["reg_no"],
                    item["github_link"]
                ])

            # Reuse the existing, tested transfer logic
            result = process_class(
                service,
                compatible_submissions,
                evaluation_url,
                class_name,
                week
            )

            all_results.append({
                "week": week,
                "class_name": class_name,
                "result": result
            })

    return {
        "available_weeks": available_weeks,
        "selected_weeks": weeks_to_process,
        "results": all_results
    }
