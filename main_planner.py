# (All imports and other functions like get_calendar_service, load_workout_plan, etc., remain the same)
import os
import json
import argparse
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
FITNESS_CALENDAR_NAME = "Fitness"
EVENT_TAG = "#WorkoutPlanner"

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE): raise FileNotFoundError(f"Error: '{CREDENTIALS_FILE}' not found.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def get_or_create_calendar(service, calendar_name):
    print(f"Checking for a calendar named '{calendar_name}'...")
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] == calendar_name:
                calendar_id = calendar_list_entry['id']
                print(f"Found existing '{calendar_name}' calendar. (ID: {calendar_id})")
                return calendar_id
        page_token = calendar_list.get('nextPageToken')
        if not page_token: break
    print(f"'{calendar_name}' calendar not found. Creating it now...")
    calendar_body = {'summary': calendar_name, 'timeZone': 'Etc/UTC'}
    try:
        created_calendar = service.calendars().insert(body=calendar_body).execute()
        calendar_id = created_calendar['id']
        print(f"Successfully created '{calendar_name}' calendar. (ID: {calendar_id})")
        return calendar_id
    except HttpError as error:
        raise ConnectionError(f"Could not create calendar: {error}")

# --- UPDATED clear_calendar_events function ---
def clear_calendar_events(service, calendar_id, start_date_str, weeks, force=False):
    """Deletes events from the calendar within a date range."""
    if force:
        print(f"\n--- FORCE CLEARING ALL events from '{FITNESS_CALENDAR_NAME}' calendar ---")
    else:
        print(f"\n--- Clearing tagged workout events from '{FITNESS_CALENDAR_NAME}' calendar ---")

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = start_date + timedelta(weeks=weeks + 52) 
    time_min = start_date.isoformat() + 'Z'
    time_max = end_date.isoformat() + 'Z'
    
    events_to_delete = []
    page_token = None
    while True:
        try:
            events_result = service.events().list(
                calendarId=calendar_id, timeMin=time_min, timeMax=time_max,
                singleEvents=True, orderBy='startTime', pageToken=page_token
            ).execute()
            events = events_result.get('items', [])
        except HttpError as error:
            print(f"An error occurred fetching events: {error}")
            return

        for event in events:
            # --- THE FIX: The 'force' flag bypasses the tag check ---
            if force or EVENT_TAG in event.get('description', ''):
                events_to_delete.append(event['id'])
        
        page_token = events_result.get('nextPageToken')
        if not page_token:
            break
            
    if not events_to_delete:
        print("No matching events found to clear in the specified range.")
        return

    print(f"Found {len(events_to_delete)} events to delete. Deleting now...")
    
    batch = service.new_batch_http_request()
    
    def callback(request_id, response, exception):
        if exception:
            print(f"  - Failed to delete event {request_id}: {exception}")
    
    for i, event_id in enumerate(events_to_delete):
        batch.add(service.events().delete(calendarId=calendar_id, eventId=event_id), callback=callback, request_id=str(i))
    
    batch.execute()
    print("Cleanup complete.")

# --- The format_event_description, load_workout_plan, and schedule_workouts functions are unchanged ---
def format_event_description(workout):
    description = f"<b>Focus: {workout.get('focus', 'N/A')}</b>\n\n"
    description += "<b>Exercises:</b>\n"
    for exercise in workout.get('exercises', []):
        description += f"• {exercise.get('name')}: {exercise.get('sets')} sets of {exercise.get('reps')} reps\n"
    description += f"\n\n<i>{EVENT_TAG}</i>"
    return description
def load_workout_plan(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: raise FileNotFoundError(f"Error: Workout plan file not found at '{filepath}'.")
    except json.JSONDecodeError: raise ValueError(f"Error: Could not parse '{filepath}'. Please ensure it is valid JSON.")
def schedule_workouts(service, fitness_calendar_id, plan, args):
    day_map = {day.lower(): i for i, day in enumerate(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])}
    try:
        training_day_indices = sorted([day_map[day.lower()] for day in args.days])
    except KeyError as e: raise ValueError(f"Error: Invalid day name '{e.args[0]}'.")
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    current_date = start_date
    print(f"\nScheduling '{plan['plan_name']}' on {', '.join(args.days).title()}...")
    total_weeks_scheduled = 0
    for phase in plan.get('phases', []):
        phase_name, duration, workouts = phase.get("phase_name"), phase.get("duration_weeks", 0), phase.get("workouts", [])
        if not workouts: continue
        print(f"\n--- Scheduling {phase_name} for {duration} weeks ---")
        workout_index = 0
        for week in range(duration):
            for day_index in training_day_indices:
                while current_date.weekday() != day_index or current_date < start_date: current_date += timedelta(days=1)
                workout = workouts[workout_index % len(workouts)]
                event = {'summary': workout['name'], 'description': format_event_description(workout), 'start': {'date': current_date.strftime('%Y-%m-%d')}, 'end': {'date': current_date.strftime('%Y-%m-%d')}}
                try:
                    created_event = service.events().insert(calendarId=fitness_calendar_id, body=event).execute()
                    print(f"  Week {total_weeks_scheduled + 1}: Created '{created_event['summary']}' on {current_date.strftime('%Y-%m-%d')}")
                except HttpError as error: print(f"An error occurred creating an event: {error}")
                workout_index += 1
                current_date += timedelta(days=1)
            total_weeks_scheduled += 1
    print(f"\nWorkout scheduling complete! Scheduled a total of {total_weeks_scheduled} weeks.")

# --- UPDATED main function ---
def main():
    parser = argparse.ArgumentParser(description="Schedule or clear a workout plan on a dedicated 'Fitness' calendar.")
    
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--schedule', nargs='+', metavar='DAY', help="Schedule workouts on the specified days (e.g., --schedule monday wednesday).")
    action_group.add_argument('--clear', action='store_true', help="Clear workout events from the Fitness calendar.")
    
    parser.add_argument('--plan', default='plan.json', help="Path to the workout plan JSON file.")
    parser.add_argument('--start-date', default=datetime.now().strftime('%Y-%m-%d'), help="The start date for scheduling or clearing in YYYY-MM-DD format.")
    # --- NEW --force flag ---
    parser.add_argument('--force', action='store_true', help="When used with --clear, deletes ALL events, not just tagged ones. Use with caution.")

    args = parser.parse_args()

    try:
        service = get_calendar_service()
        fitness_calendar_id = get_or_create_calendar(service, FITNESS_CALENDAR_NAME)
        
        if args.clear:
            if args.force:
                # Ask for confirmation for the destructive action
                confirm = input("Are you sure you want to delete ALL events from the 'Fitness' calendar? This cannot be undone. (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Operation cancelled.")
                    return
            
            plan = load_workout_plan(args.plan)
            total_weeks = sum(phase.get('duration_weeks', 0) for phase in plan.get('phases', []))
            clear_calendar_events(service, fitness_calendar_id, args.start_date, total_weeks, force=args.force)
            
        elif args.schedule:
            args.days = args.schedule
            workout_plan = load_workout_plan(args.plan)
            schedule_workouts(service, fitness_calendar_id, workout_plan, args)
        
    except (FileNotFoundError, ValueError, ConnectionError, Exception) as e:
        print(f"\nOperation failed: {e}")

if __name__ == '__main__':
    main()