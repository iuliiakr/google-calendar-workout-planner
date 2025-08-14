# Google Calendar Workout Planner

This Python script takes a multi-phase strength training plan from a JSON file and automatically schedules it on a dedicated "Fitness" calendar in a Google Calendar.

The project is designed to be flexible, allowing you to specify your training days and start date, while the plan's structure—including duration, distinct training phases, and workouts per week—is defined within the plan file itself. It also includes a robust cleanup feature to safely clear previously scheduled workouts.


## Features

-   **Progressive, Phased Plans**: Supports multi-month plans with distinct phases (e.g., "Foundation Building" vs. "Strength & Intensity") to promote long-term progressive overload.
-   **Automated Scheduling**: Populates a dedicated "Fitness" calendar for the entire duration of the plan, keeping your primary calendar clean.
-   **Smart Calendar Management**: Automatically checks for an existing "Fitness" calendar and creates one if it doesn't exist.
-   **Structured & Customizable Plans**: Uses a simple JSON format for workout plans, making them easy to create, edit, or share.
-   **Flexible Parameters**: Control your schedule with command-line arguments for the days of the week and a start date.
-   **Secure Authentication**: Uses the official Google OAuth 2.0 flow to securely access your calendar. Credentials and tokens are stored locally and are git-ignored by default.
-   **Detailed Event Descriptions**: Formats each workout's exercises, sets, and reps into the calendar event's description for easy access on your phone at the gym.
-   **Safe Cleanup Function**: Includes a `--clear` command to safely delete previously scheduled workouts, with a `--force` option to wipe all events for a clean slate.

## Setup & Installation

The Google Cloud setup is the most involved part. Please follow these steps carefully.

### 1. Prerequisites

-   Python 3.7+
-   A Google account.

### 2. Enable the Google Calendar API & Download Credentials

1.  **Create a Google Cloud Project**: Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project (e.g., "Workout Calendar Planner").
2.  **Enable the API**: In your new project, go to **APIs & Services → Library**, search for "Google Calendar API", and click **Enable**.
3.  **Configure OAuth Consent Screen**:
    -   Go to **APIs & Services → OAuth consent screen**.
    -   Choose **External** user type and click **Create**.
    -   Fill in the required app information (app name, user support email).
    -   **Crucially, add your own email address under the "Test users" section.** The app will be in "testing" mode and will only work for these users.
    -   Click **Save and Continue** through the remaining steps.
4.  **Create OAuth 2.0 Client ID**:
    -   Go to **APIs & Services → Credentials**.
    -   Click **+ CREATE CREDENTIALS** and select **OAuth client ID**.
    -   For **Application type**, select **Desktop app**.
    -   Give it a name and click **Create**.
5.  **Download the JSON File**:
    -   A popup will appear. Click **DOWNLOAD JSON**.
    -   **Rename the downloaded file to `credentials.json`** and place it in the root directory of this project. **This file is a secret and must not be shared.**

### 3. Clone the Repository & Install Dependencies

It is highly recommended to use a Python virtual environment.

```bash
# Clone the repository (replace with your username and repo name)
git clone https://github.com/your-username/gcal-workout-planner.git
cd gcal-workout-planner

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

# Usage

## First-Time Run (Authentication)

- The first time you run the script, it will automatically open a browser tab for you to grant the application permission to manage your calendar events.
- Run the script with your desired parameters (see examples below).
- A browser tab will open. Choose the Google account you listed as a "Test user".
- You will see a "Google hasn’t verified this app" warning. This is normal. Click Advanced, then "Go to [Your App Name] (unsafe)".
- Click Allow to grant permission.
- The script will complete the authentication and save a token.json file for future use.
- You will only need to do this authentication step once.


## Scheduling Workouts
The script intelligently derives the number of workouts per week and the total duration from the plan.json file.

### Example 1: Basic Usage

Schedule the default plan on Monday, Wednesday, and Friday, starting today.

```bash
python main_planner.py --schedule monday wednesday friday
```

### Example 2: Future Start Date
Schedule the plan on Tuesday, Thursday, and Saturday, starting on a specific date.

```bash
python main_planner.py --schedule tuesday thursday saturday --start-date 2024-08-01
```

## Clearing Workouts

The cleanup command allows you to safely remove previously scheduled workouts.

### Example 1: Safe Clear
This will only delete events in the "Fitness" calendar that have the script's unique #WorkoutPlanner tag in their description.

```bash
python main_planner.py --clear
```

### Example 2: Force Clear (Use with Caution)

This will delete ALL events from the "Fitness" calendar after the specified start date, regardless of whether they are tagged. This is useful for cleaning up old, untagged events from previous versions of the script.

```bash
python main_planner.py --clear --force --start-date 2024-01-01
```

### Customizing the Workout Plan
You can easily create your own plans by editing the plan.json file. The file is structured as a list of "phases." Each phase has a duration in weeks and a list of workouts to be cycled through during that phase.

```json
{
  "plan_name": "My Custom Plan",
  "phases": [
    {
      "phase_name": "Phase 1: Hypertrophy (Weeks 1-6)",
      "duration_weeks": 6,
      "workouts": [
        { "name": "Push Day", ... },
        { "name": "Pull Day", ... },
        { "name": "Leg Day", ... }
      ]
    },
    {
      "phase_name": "Phase 2: Strength (Weeks 7-10)",
      "duration_weeks": 4,
      "workouts": [ ... ]
    }
  ]
}
```
