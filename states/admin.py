from aiogram.fsm.state import StatesGroup, State

class Notify(StatesGroup):
    wait_for_content = State()

class Challenge(StatesGroup):
    waiting_for_answer = State()
    waiting_for_text = State()

class TaskManagement(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_points = State()
    waiting_for_task_id_edit = State()
    waiting_for_edit_field = State()

class PitstopManagement(StatesGroup):
    waiting_for_title = State()
    waiting_for_url = State()
    waiting_for_link_id_edit = State()

class ScheduleChallenge(StatesGroup):
    waiting_for_task_ids = State()
    waiting_for_message_text = State()
    waiting_for_send_time = State()

class ScheduleMessage(StatesGroup):
    waiting_for_message = State()
    waiting_for_send_time = State()
