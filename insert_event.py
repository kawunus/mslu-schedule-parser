from auth import get_service
from config import TARGET_CALENDAR_ID
from datetime import datetime, timezone, timedelta


def parse_time_range(date_str: str, time_range: str):
    """Parses date and time strings into timezone-aware ISO format strings."""
    start_time_str, end_time_str = time_range.split("–")
    fmt = "%d.%m.%Y %H:%M"
    start_naive = datetime.strptime(f"{date_str} {start_time_str}", fmt)
    end_naive = datetime.strptime(f"{date_str} {end_time_str}", fmt)

    tz = timezone(timedelta(hours=3))
    return (
        start_naive.replace(tzinfo=tz).isoformat(),
        end_naive.replace(tzinfo=tz).isoformat(),
    )


def prepare_event_body(
    summary, start_iso, end_iso, description, location, color_id, lesson_id
):
    """Creates a dictionary representing a Google Calendar event object."""
    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start_iso, "timeZone": "Europe/Minsk"},
        "end": {"dateTime": end_iso, "timeZone": "Europe/Minsk"},
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": 10}],
        },
        "extendedProperties": {"private": {"lesson_id": lesson_id}},
    }
    if color_id:
        event["colorId"] = str(color_id)
    return event


def sync_insert_event(event_body):
    """Synchronously inserts a new event into the target calendar."""
    service = get_service()
    result = (
        service.events().insert(calendarId=TARGET_CALENDAR_ID, body=event_body).execute()
    )
    print(f"✅ Событие создано: {result.get('summary')} ({result.get('htmlLink')})")
    return result


def sync_update_event(event_id, event_body):
    """Synchronously updates (patches) an existing event."""
    service = get_service()
    result = (
        service.events()
        .patch(calendarId=TARGET_CALENDAR_ID, eventId=event_id, body=event_body)
        .execute()
    )
    print(f"♻️ Событие обновлено: {result.get('summary')} ({result.get('htmlLink')})")
    return result


def sync_delete_event(event_id):
    """Synchronously deletes an event."""
    service = get_service()
    service.events().delete(calendarId=TARGET_CALENDAR_ID, eventId=event_id).execute()