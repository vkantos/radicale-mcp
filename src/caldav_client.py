"""
Calendar Client for MCP Calendar Application
Handles connection and communication with the calendar.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo
from models.event import Event
from models.todo import Todo

import caldav
# caldav>=3.0 does not auto-import submodules, so davclient.get_davclient
# becomes an AttributeError unless the submodule is explicitly loaded.
import caldav.davclient  # noqa: F401

logger = logging.getLogger(__name__)


def _get_tz() -> ZoneInfo:
    return ZoneInfo(os.environ.get("CALDAV_TIMEZONE", "UTC"))


def _resolve_calendar_alias(calendar_name: str) -> str:
    raw = os.environ.get("CALDAV_CALENDAR_ALIASES", "{}")
    try:
        aliases = json.loads(raw)
    except Exception:
        aliases = {}
    return aliases.get(calendar_name, calendar_name)


class CalDAVClient:
    """Client for connecting to and interacting with a calendar."""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.client = None
        self.connected = False

    def connect(self) -> bool:
        try:
            server_url = self.config_manager.get("server_url")
            username = self.config_manager.get("username")
            password = self.config_manager.get("password")
            use_ssl = self.config_manager.get("use_ssl", True)

            self.client = caldav.davclient.get_davclient(
                url=server_url,
                username=username,
                password=password,
                ssl_verify_cert=use_ssl,
            )

            self.connected = True
            logger.info("Successfully connected to the calendar")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to the calendar: {e}")
            self.connected = False
            raise

    def disconnect(self) -> None:
        if self.client:
            self.client = None
        self.connected = False
        logger.info("Disconnected from the calendar")

    def is_connected(self) -> bool:
        return self.connected

    def _get_calendar(self, calendar_name: Optional[str] = None):
        principal = self.client.principal()
        calendars = principal.calendars()
        if not calendar_name:
            if not calendars:
                raise Exception("No calendars found")
            return calendars[0]
        calendar_name = _resolve_calendar_alias(calendar_name)
        # "account/collection" → direct URL; plain name → discovery then direct
        if "/" in calendar_name:
            server_url = self.config_manager.get("server_url")
            direct_url = f"{server_url}/{calendar_name}/"
            try:
                cal = caldav.Calendar(client=self.client, url=direct_url)
                cal.objects()  # verify accessible
                return cal
            except Exception as e:
                print(f"DEBUG direct URL failed: {direct_url}, error: {e}", flush=True)
                raise Exception(f"Calendar '{calendar_name}' not found")
        for cal in calendars:
            if cal.get_display_name() == calendar_name:
                return cal
        # Fall back to direct URL for calendars not under the authenticated principal
        server_url = self.config_manager.get("server_url")
        direct_url = f"{server_url}/{calendar_name}/calendar/"
        try:
            cal = caldav.Calendar(client=self.client, url=direct_url)
            cal.objects()  # verify accessible
            return cal
        except Exception as e:
            print(f"DEBUG direct URL failed: {direct_url}, error: {e}", flush=True)
            raise Exception(f"Calendar '{calendar_name}' not found")

    def create_event(self, event: Event, calendar_name: Optional[str] = None) -> Optional[str]:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)

            tz = _get_tz()
            if event.start_time and isinstance(event.start_time, datetime):
                event.start_time = event.start_time.replace(tzinfo=None).replace(tzinfo=tz)
            if event.end_time and isinstance(event.end_time, datetime):
                event.end_time = event.end_time.replace(tzinfo=None).replace(tzinfo=tz)

            new_event = calendar.save_event(
                summary=event.title or "Untitled Event",
                description=event.description or "",
                dtstart=event.start_time,
                dtend=event.end_time,
                location=event.location,
                attendees=event.attendees,
                status=event.status,
                rrule=event.rrule if hasattr(event, "rrule") else None,
            )

            logger.info(f"Created event: {event.title or 'Untitled Event'}")
            return new_event.id
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise

    def read_event(self, event_id: str, calendar_name: Optional[str] = None) -> Optional[Event]:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            caldav_event = calendar.event(event_id)
            event_obj = self._convert_caldav_event(caldav_event)
            logger.info(f"Read event: {event_id}")
            return event_obj
        except Exception as e:
            logger.error(f"Failed to read event: {e}")
            raise

    def update_event(self, event_id: str, event_data: Dict[str, Any], calendar_name: Optional[str] = None) -> bool:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            event = calendar.event(event_id)

            for component in event.icalendar_instance.walk():
                if component.name == "VEVENT":
                    if "title" in event_data:
                        component["summary"] = event_data["title"]
                    if "description" in event_data:
                        component["description"] = event_data["description"]
                    if "start_time" in event_data:
                        component["dtstart"] = event_data["start_time"]
                    if "end_time" in event_data:
                        component["dtend"] = event_data["end_time"]
                    if "location" in event_data:
                        component["location"] = event_data["location"]
                    if "status" in event_data:
                        component["status"] = event_data["status"]
                    break

            event.save()
            logger.info(f"Updated event: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            raise

    def delete_event(self, event_id: str, calendar_name: Optional[str] = None) -> bool:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            event = calendar.event(event_id)
            event.delete()
            logger.info(f"Deleted event: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            raise

    def create_journal(self, journal_data: Dict[str, Any], calendar_name: Optional[str] = None) -> Optional[str]:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)

            new_journal = calendar.save_journal(
                summary=journal_data.get("title", "Untitled Journal"),
                description=journal_data.get("description", ""),
                dtstart=journal_data.get("date"),
                status=journal_data.get("status"),
            )

            logger.info(f"Created journal: {journal_data.get('title', 'Unknown')}")
            return new_journal.id
        except Exception as e:
            logger.error(f"Failed to create journal: {e}")
            raise

    def read_journal(self, journal_id: str, calendar_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            journal = calendar.journal(journal_id)

            journal_data = {
                "id": journal_id,
                "title": "",
                "description": "",
                "date": "",
                "status": "",
            }

            for component in journal.icalendar_instance.walk():
                if component.name == "VJOURNAL":
                    journal_data["title"] = str(component.get("summary", ""))
                    journal_data["description"] = str(component.get("description", ""))

                    dtstart = component.get("dtstart")
                    if dtstart:
                        journal_data["date"] = dtstart.dt.strftime("%m/%d/%Y %H:%M")

                    journal_data["status"] = str(component.get("status", ""))
                    break

            logger.info(f"Read journal: {journal_id}")
            return journal_data
        except Exception as e:
            logger.error(f"Failed to read journal: {e}")
            raise

    def update_journal(self, journal_id: str, journal_data: Dict[str, Any], calendar_name: Optional[str] = None) -> bool:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            journal = calendar.journal(journal_id)

            for component in journal.icalendar_instance.walk():
                if component.name == "VJOURNAL":
                    if "title" in journal_data:
                        component["summary"] = journal_data["title"]
                    if "description" in journal_data:
                        component["description"] = journal_data["description"]
                    if "date" in journal_data:
                        component["dtstart"] = journal_data["date"]
                    if "status" in journal_data:
                        component["status"] = journal_data["status"]
                    break

            journal.save()
            logger.info(f"Updated journal: {journal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update journal: {e}")
            raise

    def delete_journal(self, journal_id: str, calendar_name: Optional[str] = None) -> bool:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            journal = calendar.journal(journal_id)
            journal.delete()
            logger.info(f"Deleted journal: {journal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete journal: {e}")
            raise

    def create_todo(self, todo: Todo, calendar_name: Optional[str] = None) -> Optional[str]:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)

            tz = _get_tz()
            if todo.due_date and isinstance(todo.due_date, datetime):
                todo.due_date = todo.due_date.replace(tzinfo=None).replace(tzinfo=tz)
            if todo.completion_date and isinstance(todo.completion_date, datetime):
                todo.completion_date = todo.completion_date.replace(tzinfo=None).replace(tzinfo=tz)

            new_todo = calendar.save_todo(
                summary=todo.title or "Untitled Todo",
                description=getattr(todo, "description", ""),
                priority=getattr(todo, "priority", 5),
                status=getattr(todo, "status", None),
                due=todo.due_date,
                completed=getattr(todo, "completion_date", None),
            )

            logger.info(f"Created todo: {todo.title or 'Unknown'}")
            return new_todo.id
        except Exception as e:
            logger.error(f"Failed to create todo: {e}")
            raise

    def read_todo(self, todo_id: str, calendar_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            todo = calendar.todo(todo_id)

            todo_data = {
                "id": todo_id,
                "title": "",
                "description": "",
                "priority": 5,
                "status": "",
                "due_date": "",
                "completed_date": "",
            }

            for component in todo.icalendar_instance.walk():
                if component.name == "VTODO":
                    todo_data["title"] = str(component.get("summary", ""))
                    todo_data["description"] = str(component.get("description", ""))

                    priority = component.get("priority")
                    if priority:
                        todo_data["priority"] = int(priority)

                    todo_data["status"] = str(component.get("status", ""))

                    due = component.get("due")
                    if due:
                        todo_data["due_date"] = due.dt.strftime("%m/%d/%Y %H:%M")

                    completed = component.get("completed")
                    if completed:
                        todo_data["completed_date"] = completed.dt.strftime("%m/%d/%Y %H:%M")
                    break

            logger.info(f"Read todo: {todo_id}")
            return todo_data
        except Exception as e:
            logger.error(f"Failed to read todo: {e}")
            raise

    def update_todo(self, todo_id: str, todo_data: Dict[str, Any], calendar_name: Optional[str] = None) -> bool:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            todo = calendar.todo(todo_id)

            for component in todo.icalendar_instance.walk():
                if component.name == "VTODO":
                    if "title" in todo_data:
                        component["summary"] = todo_data["title"]
                    if "description" in todo_data:
                        component["description"] = todo_data["description"]
                    if "priority" in todo_data:
                        component["priority"] = todo_data["priority"]
                    if "status" in todo_data:
                        component["status"] = todo_data["status"]
                    if "due_date" in todo_data:
                        component["due"] = todo_data["due_date"]
                    if "completed_date" in todo_data:
                        component["completed"] = todo_data["completed_date"]
                    break

            todo.save()
            logger.info(f"Updated todo: {todo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update todo: {e}")
            raise

    def delete_todo(self, todo_id: str, calendar_name: Optional[str] = None) -> bool:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)
            todo = calendar.todo(todo_id)
            todo.delete()
            logger.info(f"Deleted todo: {todo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete todo: {e}")
            raise

    def _convert_caldav_event(self, caldav_event) -> Event:
        event_data = {
            "id": caldav_event.id,
            "title": "",
            "description": "",
            "start_time": None,
            "end_time": None,
            "location": "",
            "status": "",
            "attendees": [],
            "rrule": None,
        }

        for component in caldav_event.icalendar_instance.walk():
            if component.name == "VEVENT":
                event_data["title"] = str(component.get("summary", ""))
                event_data["description"] = str(component.get("description", ""))

                dtstart = component.get("dtstart")
                if dtstart:
                    event_data["start_time"] = dtstart.dt

                dtend = component.get("dtend")
                if dtend:
                    event_data["end_time"] = dtend.dt

                event_data["location"] = str(component.get("location", ""))
                event_data["status"] = str(component.get("status", ""))

                attendees = component.get("attendee", [])
                if attendees:
                    if isinstance(attendees, list):
                        event_data["attendees"] = [str(a) for a in attendees]
                    else:
                        event_data["attendees"] = [str(attendees)]

                rrule = component.get("rrule")
                if rrule:
                    event_data["rrule"] = rrule

                if not event_data["id"]:
                    uid = component.get("uid")
                    if uid:
                        event_data["id"] = str(uid)

                break

        event_obj = Event(
            title=event_data["title"],
            description=event_data["description"],
            start_time=event_data["start_time"],
            end_time=event_data["end_time"],
            location=event_data["location"],
            attendees=event_data["attendees"],
            status=event_data["status"],
            rrule=event_data.get("rrule"),
        )
        event_obj.id = event_data["id"]
        return event_obj

    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_name: Optional[str] = None,
    ) -> list:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)

            if start_date and end_date:
                events = calendar.events(start=start_date, end=end_date)
            else:
                events = calendar.events()

            event_list = [self._convert_caldav_event(event) for event in events]
            logger.info(f"Retrieved {len(event_list)} events")
            return event_list

        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            raise

    def get_todos(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_name: Optional[str] = None,
    ) -> list:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)

            if start_date and end_date:
                todos = calendar.todos(start=start_date, end=end_date)
            else:
                todos = calendar.todos()

            todo_list = []
            for todo in todos:
                todo_data = {
                    "id": todo.id,
                    "title": "",
                    "description": "",
                    "priority": 5,
                    "status": "",
                    "due_date": None,
                    "completion_date": None,
                }

                for component in todo.icalendar_instance.walk():
                    if component.name == "VTODO":
                        todo_data["title"] = str(component.get("summary", ""))
                        todo_data["description"] = str(component.get("description", ""))

                        priority = component.get("priority")
                        if priority:
                            todo_data["priority"] = int(priority)

                        todo_data["status"] = str(component.get("status", ""))

                        due = component.get("due")
                        if due:
                            todo_data["due_date"] = due.dt

                        completed = component.get("completed")
                        if completed:
                            todo_data["completion_date"] = completed.dt

                        if not todo_data["id"]:
                            uid = component.get("uid")
                            if uid:
                                todo_data["id"] = str(uid)
                        break

                todo_obj = Todo(
                    title=todo_data["title"],
                    description=todo_data["description"],
                    due_date=todo_data["due_date"],
                    completion_date=todo_data["completion_date"],
                    status=todo_data["status"],
                    priority=todo_data["priority"],
                )
                todo_obj.id = todo_data["id"]
                todo_list.append(todo_obj)

            logger.info(f"Retrieved {len(todo_list)} todos")
            return todo_list

        except Exception as e:
            logger.error(f"Failed to retrieve todos: {e}")
            raise

    def get_journals(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        calendar_name: Optional[str] = None,
    ) -> list:
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            calendar = self._get_calendar(calendar_name)

            if start_date and end_date:
                journals = calendar.journals(start=start_date, end=end_date)
            else:
                journals = calendar.journals()

            journal_list = []
            for journal in journals:
                journal_data = self.read_journal(journal.id, calendar_name)
                journal_list.append(journal_data)

            logger.info(f"Retrieved {len(journal_list)} journals")
            return journal_list
        except Exception as e:
            logger.error(f"Failed to retrieve journals: {e}")
            raise
