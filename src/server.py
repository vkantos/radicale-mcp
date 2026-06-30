#!/usr/bin/env python3
"""
FastMCP Server Implementation for calendar Operations
This demonstrates how to use the fastmcp library with the existing calendar functionality.
"""

from fastmcp import FastMCP
from caldav_client import CalDAVClient
from config_manager import ConfigManager
from models.event import Event
from models.todo import Todo
from datetime import datetime
from typing import Optional
import os
from zoneinfo import ZoneInfo

# Initialize the MCP server
mcp = FastMCP("Radicale MCP server 🚀")


def _parse_to_tz(dt_str: str) -> datetime:
    """Parse ISO datetime string and convert to target timezone."""
    dt = datetime.fromisoformat(dt_str)
    target_tz_name = os.getenv("CALDAV_TIMEZONE", "UTC")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(target_tz_name))

    try:
        target_tz = ZoneInfo(target_tz_name)
    except Exception:
        target_tz = ZoneInfo("UTC")
    return dt.astimezone(target_tz)


# Initialize configuration and client
config_manager = ConfigManager()
caldav_client = CalDAVClient(config_manager)


def _ensure_connected() -> Optional[dict]:
    """Return error dict if connection fails, None if connected."""
    if not caldav_client.is_connected():
        success = caldav_client.connect()
        if not success:
            return {"error": "Failed to connect to the calendar"}
    return None


@mcp.tool
def get_events(calendar_name: Optional[str] = None) -> list:
    """Get all events from the calendar. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return [err]
        events = caldav_client.get_events(calendar_name=calendar_name)
        return [event.to_dict() for event in events]
    except Exception as e:
        return [{"error": f"Failed to get events: {str(e)}"}]


@mcp.tool
def connect() -> dict:
    """Connect to the calendar."""
    try:
        success = caldav_client.connect()
        if success:
            return {"status": "connected", "message": "Successfully connected to the calendar"}
        else:
            return {"status": "failed", "message": "Failed to connect to the calendar"}
    except Exception as e:
        return {"status": "error", "message": f"Error connecting to the calendar: {str(e)}"}


@mcp.tool
def reconnect() -> dict:
    """Reconnect to the calendar."""
    try:
        caldav_client.disconnect()
        success = caldav_client.connect()
        if success:
            return {"status": "reconnected", "message": "Successfully reconnected to the calendar"}
        else:
            return {"status": "failed", "message": "Failed to reconnect to the calendar"}
    except Exception as e:
        return {"status": "error", "message": f"Error reconnecting to the calendar: {str(e)}"}


@mcp.tool
def create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    calendar_name: Optional[str] = None,
) -> dict:
    """Create a new event on the calendar. Time in ISO format (e.g., '2026-01-14T02:16:17.478'). description and location are optional notes/place for the event. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err

        start_dt = _parse_to_tz(start_time)
        end_dt = _parse_to_tz(end_time)

        event = Event(
            title=title,
            description=description,
            location=location,
            start_time=start_dt,
            end_time=end_dt,
            calendar_name=calendar_name,
        )
        created_event_id = caldav_client.create_event(event, calendar_name=calendar_name)
        if not created_event_id:
            return {"error": "Failed to create event"}
        event_obj = caldav_client.read_event(created_event_id, calendar_name=calendar_name)
        if hasattr(event_obj, "to_dict"):
            return event_obj.to_dict()
        return {"id": created_event_id}
    except Exception as e:
        return {"error": f"Failed to create event: {str(e)}"}


@mcp.tool
def create_recurring_event(
    title: str,
    start_time: str,
    end_time: str,
    frequency: str,
    interval: int = 1,
    count: int = None,
    description: str = "",
    location: str = "",
    calendar_name: Optional[str] = None,
) -> dict:
    """Create a recurring event on the calendar. Time in ISO format (e.g., '2026-01-14T02:16:17.478'). Frequency (YEARLY, MONTHLY, WEEKLY, DAILY). Interval between recurrences (default: 1). Number of occurrences (optional). description and location are optional notes/place for the event. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err

        rrule = {"FREQ": frequency.upper()}
        if interval != 1:
            rrule["INTERVAL"] = interval
        if count:
            rrule["COUNT"] = count

        start_dt = _parse_to_tz(start_time)
        end_dt = _parse_to_tz(end_time)

        event = Event(
            title=title,
            description=description,
            location=location,
            start_time=start_dt,
            end_time=end_dt,
            rrule=rrule,
            calendar_name=calendar_name,
        )
        created_event_id = caldav_client.create_event(event, calendar_name=calendar_name)
        if not created_event_id:
            return {"error": "Failed to create recurring event"}
        event_obj = caldav_client.read_event(created_event_id, calendar_name=calendar_name)
        if hasattr(event_obj, "to_dict"):
            return event_obj.to_dict()
        return {"id": created_event_id}
    except Exception as e:
        return {"error": f"Failed to create recurring event: {str(e)}"}


@mcp.tool
def get_todos(calendar_name: Optional[str] = None) -> list:
    """Get all todos from the calendar. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return [err]
        todos = caldav_client.get_todos(calendar_name=calendar_name)
        return [todo.to_dict() for todo in todos]
    except Exception as e:
        return [{"error": f"Failed to get todos: {str(e)}"}]


@mcp.tool
def get_journals(calendar_name: Optional[str] = None) -> list:
    """Get all journals from the calendar. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return [err]
        journals = caldav_client.get_journals(calendar_name=calendar_name)
        return journals
    except Exception as e:
        return [{"error": f"Failed to get journals: {str(e)}"}]


@mcp.tool
def delete_event(id: str, calendar_name: Optional[str] = None) -> dict:
    """Delete an event from the calendar. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err
        result = caldav_client.delete_event(id, calendar_name=calendar_name)
        return {"deleted": result}
    except Exception as e:
        return {"error": f"Failed to delete event: {str(e)}"}


@mcp.tool
def get_event(id: str, calendar_name: Optional[str] = None) -> dict:
    """Retrieve a single event by ID. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err
        event = caldav_client.read_event(id, calendar_name=calendar_name)
        if event is None:
            return {"error": f"Event {id} not found"}
        if hasattr(event, "to_dict"):
            return event.to_dict()
        return {"id": id}
    except Exception as e:
        return {"error": f"Failed to get event: {str(e)}"}


@mcp.tool
def update_event(
    id: str,
    title: str = None,
    description: str = None,
    start_time: str = None,
    end_time: str = None,
    location: str = None,
    status: str = None,
    calendar_name: Optional[str] = None,
) -> dict:
    """Update an existing event by ID. Only fields you pass are modified; omit a field to leave it unchanged. Times in ISO format (e.g., '2026-01-14T02:16:17.478'). status is one of CONFIRMED, TENTATIVE, CANCELLED. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err

        event_data = {}
        if title is not None:
            event_data["title"] = title
        if description is not None:
            event_data["description"] = description
        if start_time is not None:
            event_data["start_time"] = _parse_to_tz(start_time)
        if end_time is not None:
            event_data["end_time"] = _parse_to_tz(end_time)
        if location is not None:
            event_data["location"] = location
        if status is not None:
            event_data["status"] = status

        if not event_data:
            return {"error": "No fields provided to update"}

        result = caldav_client.update_event(id, event_data, calendar_name=calendar_name)
        if not result:
            return {"error": "Failed to update event"}
        updated = caldav_client.read_event(id, calendar_name=calendar_name)
        if updated is not None and hasattr(updated, "to_dict"):
            return updated.to_dict()
        return {"id": id, "updated": True}
    except Exception as e:
        return {"error": f"Failed to update event: {str(e)}"}


@mcp.tool
def delete_todo(id: str, calendar_name: Optional[str] = None) -> dict:
    """Delete a todo from the calendar. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err
        result = caldav_client.delete_todo(id, calendar_name=calendar_name)
        return {"deleted": result}
    except Exception as e:
        return {"error": f"Failed to delete todo: {str(e)}"}


@mcp.tool
def create_journal(
    date: str,
    title: str = "",
    content: str = "",
    tags_comma_seperated: str = "",
    categories_comma_seperated: str = "",
    priority: int = 5,
    url: str = "",
    calendar_name: Optional[str] = None,
) -> dict:
    """Create a new journal entry on the calendar. Dates in ISO format. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err
        journal_date = _parse_to_tz(date) if date else None
        journal_data = {
            "date": journal_date,
            "title": title,
            "description": content,
            "tags": [t.strip() for t in tags_comma_seperated.split(",") if t.strip()],
            "categories": [c.strip() for c in categories_comma_seperated.split(",") if c.strip()],
            "priority": priority,
            "url": url,
        }
        created_journal_id = caldav_client.create_journal(journal_data, calendar_name=calendar_name)
        return {"id": created_journal_id}
    except Exception as e:
        return {"error": f"Failed to create journal: {str(e)}"}


@mcp.tool
def delete_journal(id: str, calendar_name: Optional[str] = None) -> dict:
    """Delete a journal entry from the calendar. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err
        result = caldav_client.delete_journal(id, calendar_name=calendar_name)
        return {"deleted": result}
    except Exception as e:
        return {"error": f"Failed to delete journal: {str(e)}"}


@mcp.tool
def get_journal(journal_id: str, calendar_name: Optional[str] = None) -> dict:
    """Retrieve a journal entry by its ID. calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err
        journal = caldav_client.read_journal(journal_id, calendar_name=calendar_name)
        return journal
    except Exception as e:
        return {"error": f"Failed to get journal: {str(e)}"}


@mcp.tool
def create_todo(
    title: str,
    due_date: str,
    description: str = "",
    completion_date: str = None,
    status: str = "NEEDS-ACTION",
    priority: int = 5,
    categories_comma_seperated: str = "",
    url: str = "",
    percent_complete: int = 0,
    calendar_name: Optional[str] = None,
) -> dict:
    """Create a new todo on the calendar. Time in ISO format (e.g., '2026-01-14T02:16:17.478'). calendar_name selects which calendar to use (default: first)."""
    try:
        err = _ensure_connected()
        if err:
            return err

        due_dt = _parse_to_tz(due_date) if due_date else None
        completed_dt = _parse_to_tz(completion_date) if completion_date else None

        todo = Todo(
            title=title,
            description=description,
            due_date=due_dt,
            completion_date=completed_dt,
            status=status,
            priority=priority,
            categories=categories_comma_seperated.split(","),
            url=url,
            percent_complete=percent_complete,
            calendar_name=calendar_name,
        )
        created_todo_id = caldav_client.create_todo(todo, calendar_name=calendar_name)
        return {"id": created_todo_id}
    except Exception as e:
        return {"error": f"Failed to create todo: {str(e)}"}


def start_server():
    """Start the MCP server using STDIO transport."""
    mcp.run()


if __name__ == "__main__":
    start_server()
