import requests, time, random, string, json
from datetime import datetime, timedelta
from collections import defaultdict

STOP_WORDS = ["Пашкевич", "Иванов"]

def random_id(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def iso_today():
    return datetime.now().strftime("%Y-%m-%d")


def normalize_teacher(f, n, o):
    parts = [p for p in [f, n, o] if p]
    if not parts:
        return ""
    initials = "".join([f" {p[0]}." for p in parts[1:]])
    return f"{parts[0]}{initials}"


def normalize_classroom(classroom):
    if not classroom or classroom.lower().startswith("ауд"):
        return "Кабинет не найден, но скоро появится..."
    return classroom[2:]


def fetch_schedule(id_group, start_date=None, end_date=None):
    if start_date is None:
        start_date = iso_today()
    if end_date is None:
        end_date = "2025-12-31"

    url = "http://www.timetable.bsufl.by/api/api/groupschedule"
    params = {"startDate": start_date, "endDate": end_date, "idGroup": str(id_group)}
    headers = {
        "Origin": "http://timetable.bsufl.by",
        "Referer": "http://timetable.bsufl.by/schedule",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "X-Request-Id": f"{random_id()}--{random_id(15)}",
        "X-Request-Origin": "http://timetable.bsufl.by",
        "X-Timestamp": str(int(time.time() * 1000)),
    }

    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    data = r.json()

    grouped = defaultdict(list)
    for item in data:
        if any(w.lower() in item.get("discipline", "").lower() for w in STOP_WORDS):
            continue
        if any(w.lower() in item.get("teacherF", "").lower() for w in STOP_WORDS):
            continue
        try:
            base = datetime.strptime(item["dateIn"], "%Y-%m-%d")
            real_date = base + timedelta(days=item["dayNumber"] - 1)
            date_key = real_date.strftime("%d.%m.%Y")

            teacher = normalize_teacher(item.get("teacherF"), item.get("teacherN"), item.get("teacherO"))
            classroom = normalize_classroom(item.get("classroom"))
            grouped[date_key].append({
                "lessonNumber": item["lessonNumber"],
                "timeRange": f"{item['timeIn']}–{item['timeOut']}",
                "discipline": item["discipline"],
                "disciplineType": item["disciplineType"],
                "teacher": teacher,
                "day": item["day"],
                "classroom": classroom,
            })
        except Exception as e:
            print(f"⚠️ Ошибка при обработке: {e}")

    structured = []
    for date_key in sorted(grouped.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y")):
        lessons = sorted(grouped[date_key], key=lambda x: x["lessonNumber"])
        structured.append({"date": date_key, "day": lessons[0]["day"], "lessons": lessons})
    return structured
