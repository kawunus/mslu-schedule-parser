import asyncio
from datetime import datetime, timezone, timedelta
from auth import get_service
from parser import fetch_schedule
from insert_event import (
    sync_insert_event,
    sync_update_event,
    sync_delete_event,
    parse_time_range,
    prepare_event_body,
)
from config import (
    TARGET_CALENDAR_ID,
    UPDATE_INTERVAL,
    COLORS,
    PAUSE_BETWEEN_REQUESTS,
)

TYPE_TO_COLOR = {
    "Сем": COLORS.get("Сем"),
    "Практ": COLORS.get("Практ"),
    "Лек": COLORS.get("Лек"),
}


def generate_lesson_id(date, lesson):
    """Generates a unique, consistent ID for a lesson based on its core properties."""
    return f"{date}|{lesson['timeRange']}|{lesson['teacher']}|{lesson['classroom']}"


def get_lesson_id_from_event(event):
    """Extracts the unique lesson_id from an event's extendedProperties, with a fallback to the description."""
    private_props = event.get("extendedProperties", {}).get("private", {})
    if private_props and "lesson_id" in private_props:
        return private_props["lesson_id"]

    description = event.get("description", "")
    if "[AUTO-UNI]" in description:
        return description.split("[AUTO-UNI]")[0].strip()

    return None


def needs_update(existing_event, new_lesson_details):
    """Checks if an existing event's data differs from the new schedule details."""
    ex_start = existing_event.get("start", {}).get("dateTime", "")
    ex_end = existing_event.get("end", {}).get("dateTime", "")
    ex_summary = existing_event.get("summary", "")
    ex_description = existing_event.get("description", "")
    ex_location = existing_event.get("location", "")
    ex_color_id = existing_event.get("colorId")

    new_color_id = new_lesson_details.get("color_id")

    if (
        ex_start != new_lesson_details["start_iso"]
        or ex_end != new_lesson_details["end_iso"]
        or ex_summary != new_lesson_details["summary"]
        or ex_description != new_lesson_details["description"]
        or ex_location != new_lesson_details["location"]
        or str(ex_color_id) != str(new_color_id)
    ):
        return True

    return False


async def update_schedule():
    """
    Fetches the university schedule and synchronizes it with Google Calendar by creating,
    updating, or deleting events as needed.
    """
    service = get_service()

    print("📥 Получение нового расписания с сервера...")
    new_schedule_list = await asyncio.to_thread(fetch_schedule, 224003553)

    if not new_schedule_list:
        print("ℹ️ Новое расписание пустое. Завершение синхронизации.")
        return

    first_date_str = new_schedule_list[0]["date"]
    minsk_tz = timezone(timedelta(hours=3))
    time_min_dt = datetime.strptime(first_date_str, "%d.%m.%Y").replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=minsk_tz
    )
    time_min_iso = time_min_dt.isoformat()

    print(f"🔍 Получение существующих событий из Google Calendar начиная с {first_date_str}...")
    events_result = await asyncio.to_thread(
        lambda: service.events()
        .list(
            calendarId=TARGET_CALENDAR_ID,
            timeMin=time_min_iso,
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        )
        .execute()
    )

    existing_events_map = {}
    for event in events_result.get("items", []):
        lesson_id = get_lesson_id_from_event(event)
        if lesson_id:
            existing_events_map[lesson_id] = event
    print(f"🗓 Найдено {len(existing_events_map)} существующих событий в календаре.")

    new_lessons_map = {}
    for day in new_schedule_list:
        for lesson in day["lessons"]:
            lesson_id = generate_lesson_id(day["date"], lesson)
            start_iso, end_iso = parse_time_range(day["date"], lesson["timeRange"])
            summary = f"{lesson['discipline']} ({lesson['disciplineType']})"
            description = f"{lesson_id} [AUTO-UNI]"

            teacher = lesson.get("teacher", "")
            classroom = lesson.get("classroom", "")
            location_parts = []
            if classroom and "не найден" not in classroom:
                location_parts.append(f"В {classroom}")
            if teacher:
                location_parts.append(f"Препод: {teacher}")
            location = ". ".join(location_parts)

            new_lessons_map[lesson_id] = {
                "lesson_id": lesson_id,
                "summary": summary,
                "description": description,
                "start_iso": start_iso,
                "end_iso": end_iso,
                "location": location,
                "color_id": TYPE_TO_COLOR.get(lesson["disciplineType"]),
            }
    print(f"📚 Найдено {len(new_lessons_map)} актуальных занятий в расписании.")

    existing_ids = set(existing_events_map.keys())
    new_ids = set(new_lessons_map.keys())

    ids_to_delete = existing_ids - new_ids
    ids_to_create = new_ids - existing_ids
    ids_to_check_for_updates = existing_ids.intersection(new_ids)

    for lesson_id in ids_to_delete:
        event = existing_events_map[lesson_id]
        try:
            await asyncio.to_thread(sync_delete_event, event["id"])
            print(f"🗑 Удалено устаревшее событие: {event.get('summary')} ({lesson_id})")
            await asyncio.sleep(PAUSE_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"⚠️ Ошибка удаления '{event.get('summary')}': {e}")

    for lesson_id in ids_to_create:
        details = new_lessons_map[lesson_id]
        event_body = prepare_event_body(**details)
        try:
            await asyncio.to_thread(sync_insert_event, event_body)
            await asyncio.sleep(PAUSE_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"⚠️ Ошибка создания '{details['summary']}': {e}")

    for lesson_id in ids_to_check_for_updates:
        existing_event = existing_events_map[lesson_id]
        new_details = new_lessons_map[lesson_id]

        if needs_update(existing_event, new_details):
            event_body = prepare_event_body(**new_details)
            try:
                await asyncio.to_thread(
                    sync_update_event, existing_event["id"], event_body
                )
                await asyncio.sleep(PAUSE_BETWEEN_REQUESTS)
            except Exception as e:
                print(f"⚠️ Ошибка обновления '{new_details['summary']}': {e}")
        else:
            print(f"⏭ Пропускаем актуальное событие: {existing_event.get('summary')}")


async def scheduler():
    """Main scheduler loop to run the update process periodically."""
    while True:
        print("🔄 Обновление расписания...")
        try:
            await update_schedule()
            print("✅ Расписание успешно обновлено.")
        except Exception as e:
            print(f"⚠️ Критическая ошибка в цикле обновления: {e}")
        print(f"⏳ Следующее обновление через {UPDATE_INTERVAL} секунд.")
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(scheduler())