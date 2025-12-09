# Tandem ToDo Bot

Telegram bot built with **aiogram**, **PostgreSQL**, **matplotlib**, and **APScheduler** for challenge tracking in pairs (tandems).

### Current Features
- Administrators create challenges and set deadlines.
- Users complete these challenges and track their progress.
- Progress is visualized using matplotlib diagrams.
- Challenge data is stored in PostgreSQL.
- Scheduled tasks handle reminders and scheduled updates.

### Status
This is a work-in-progress version.  
- The bot is still under development and some features are not yet implemented.  
- Certain parts of the logic may change.  
- Future plans include improved analytics, onboarding, and admin tools.

### Structure
- `config/` — configuration files.  
- `handlers/` — Telegram command handlers (admins and users).  
- `keyboards/` — inline and reply keyboards.  
- `middlewares/` — aiogram middlewares.  
- `services/` — database work, diagram generation, message processing, and scheduler logic.  
- `states/` — FSM states for aiogram.  
- `logs/` — log files and logging output.  
- `photos/` — image storage.

### Usage
Currently not fully operational.  
Please reach out if you would like access to try out the bot or contribute.

### About
This repository is the starting point for the Tandem ToDo Bot project.  
The project is actively being developed and new features will be added soon.
