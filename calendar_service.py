from google.oauth2 import service_account
from googleapiclient.discovery import build
import dateparser
from datetime import timedelta
from datetime import datetime, timedelta
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'vet-agent-493414-ca8ade63048e.json'


credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)
IST = pytz.timezone('Asia/Kolkata')

def is_slot_available(start_dt, end_time):
    try:
        events = service.events().list(
            calendarId='sinha.divyshekhar2004@gmail.com',
            timeMin=start_dt.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
    except Exception as e:
        print("Error checking calendar availability:", e)
        return False

    return len(events.get('items', [])) == 0

def find_next_slot(start_dt):
    while True:
        start_dt += timedelta(minutes=30)
        end_dt = start_dt + timedelta(minutes=30)

        if is_slot_available(start_dt, end_dt):
            return start_dt

def create_event(owner_name, pet_name, date_str, time_str):
    dt = dateparser.parse(f"{date_str} {time_str}")
    if not dt:
        return "❌ Invalid date/time format. Please try again."

    dt = IST.localize(dt)

    end_time = dt+timedelta(minutes=30)
    if not is_slot_available(dt, end_time):
        next_slot = find_next_slot(dt)

        return {
            "success": False,
            "message": f"❌ Slot booked. Next available: {next_slot.strftime('%d %B %Y %I:%M %p')}"
        }

    event = {
        'summary': f"Vet Appointment for {pet_name} (Owner: {owner_name})",
        'start': {
            'dateTime': dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        
    }
    try:
        event = service.events().insert(calendarId='sinha.divyshekhar2004@gmail.com', body=event).execute()
        return {
            "success": True,
            "message": "✅ Appointment booked!",
            "event_link": event.get('htmlLink')
        }
    except Exception as e:
        print("Error creating calendar event:", e)
        return {
            "success": False,
            "message": "❌ Failed to create event"
        }
# def find_next_slot(dt):
#     while True:
#         dt += timedelta(minutes=30)
#         end = dt + timedelta(minutes=30)

#         if is_slot_available(dt, end):
#             return dt