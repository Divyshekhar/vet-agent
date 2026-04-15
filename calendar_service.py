import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build
import dateparser
from datetime import timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'vet-agent-493414-ca8ade63048e.json'


credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)

def create_event(owner_name, pet_name, date_str, time_str):
    dt = dateparser.parse(f"{date_str} {time_str}")
    if not dt:
        return "Invalid date/time format. Please try again."
    end_time = dt+timedelta(minutes=30)
    
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
    event = service.events().insert(calendarId='sinha.divyshekhar2004@gmail.com', body=event).execute()
    return {
        "event_link": event.get('htmlLink')
    }
    
    