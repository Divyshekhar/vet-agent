from db import save_appointment

def book_appointment(owner_name, pet_name, date, time):
    appointment_data = {
        "owner_name": owner_name,
        "pet_name": pet_name,
        "date": date,
        "time": time
    }
    save_appointment(appointment_data)
    
    return f"✅ Appointment booked for {pet_name} on {date} at {time}."