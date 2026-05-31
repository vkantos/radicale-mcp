"""
Calendar Client for MCP Calendar Application
Handles connection and communication with the calendar.
"""

import logging
from typing import Dict, Any, Optional
from models.event import Event
from models.todo import Todo

import caldav
# caldav>=3.0 does not auto-import submodules, so davclient.get_davclient
# becomes an AttributeError unless the submodule is explicitly loaded.
import caldav.davclient  # noqa: F401

logger = logging.getLogger(__name__)


class CalDAVClient:
    """Client for connecting to and interacting with a calendar."""

    def __init__(self, config_manager):
        """
        Initialize the CalDAV client.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.client = None
        self.connected = False

    def connect(self) -> bool:
        """
        Establish connection to the calendar.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            server_url = self.config_manager.get("server_url")
            username = self.config_manager.get("username")
            password = self.config_manager.get("password")
            use_ssl = self.config_manager.get("use_ssl", True)

            # Create connection
            if use_ssl:
                self.client = caldav.davclient.get_davclient(
                    url=server_url,
                    username=username,
                    password=password,
                    ssl_verify_cert=True,
                )
            else:
                self.client = caldav.davclient.get_davclient(
                    url=server_url,
                    username=username,
                    password=password,
                    ssl_verify_cert=False,
                )

            self.connected = True
            logger.info("Successfully connected to the calendar")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to the calendar: {e}")
            self.connected = False
            raise  # Propagate the exception

    def disconnect(self) -> None:
        """Close the connection to the calendar."""
        if self.client:
            # In a real implementation, we would close the connection
            self.client = None
        self.connected = False
        logger.info("Disconnected from the calendar")

    def is_connected(self) -> bool:
        """
        Check if client is connected.

        Returns:
            True if connected, False otherwise
        """
        return self.connected

    def create_event(self, event: Event) -> Optional[str]:
        """
        Create a new event in the CalDAV server.

        Args:
            event: Event object containing event data

        Returns:
            ID of created event or None if failed
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Create event using calendar.save_event with parameters
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

            # Return the event ID
            logger.info(f"Created event: {event.title or 'Untitled Event'}")
            return new_event.id
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise  # Propagate the exception

    def read_event(self, event_id: str) -> Optional[Event]:
        """
        Read an event from the CalDAV server.

        Args:
            event_id: ID of the event to read

        Returns:
            Event object or None if not found
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            principal = self.client.principal()
            calendar = principal.calendars()[0]
            caldav_event = calendar.event(event_id)
            event_obj = self._convert_caldav_event(caldav_event)
            logger.info(f"Read event: {event_id}")
            return event_obj
        except Exception as e:
            logger.error(f"Failed to read event: {e}")
            raise

    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """
        Update an existing event in the CalDAV server.

        Args:
            event_id: ID of the event to update
            event_data: Dictionary containing updated event data

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the event by ID
            event = calendar.event(event_id)

            # Update the event properties by modifying the icalendar instance
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
                    break  # We only need to modify the first VEVENT

            # Save the updated event
            event.save()

            logger.info(f"Updated event: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            raise  # Propagate the exception

    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from the CalDAV server.

        Args:
            event_id: ID of the event to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the event by ID
            event = calendar.event(event_id)

            # Delete the event
            event.delete()

            logger.info(f"Deleted event: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            raise  # Propagate the exception

    def create_journal(self, journal_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new journal entry in the CalDAV server.

        Args:
            journal_data: Dictionary containing journal data

        Returns:
            ID of created journal or None if failed
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Create journal entry using calendar.save_journal with parameters
            new_journal = calendar.save_journal(
                summary=journal_data.get("title", "Untitled Journal"),
                description=journal_data.get("description", ""),
                dtstart=journal_data.get("date"),
                status=journal_data.get("status"),
            )

            # Return the journal ID
            logger.info(f"Created journal: {journal_data.get('title', 'Unknown')}")
            return new_journal.id
        except Exception as e:
            logger.error(f"Failed to create journal: {e}")
            raise  # Propagate the exception

    def read_journal(self, journal_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a journal entry from the CalDAV server.

        Args:
            journal_id: ID of the journal entry to read

        Returns:
            Dictionary containing journal data or None if not found
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the journal by ID
            journal = calendar.journal(journal_id)

            # Convert to dictionary format
            journal_data = {
                "id": journal_id,
                "title": "",
                "description": "",
                "date": "",
                "status": "",
            }

            # Walk through components to find VJOURNAL
            for component in journal.icalendar_instance.walk():
                if component.name == "VJOURNAL":
                    journal_data["title"] = str(component.get("summary", ""))
                    journal_data["description"] = str(component.get("description", ""))

                    # Handle date/time values
                    dtstart = component.get("dtstart")
                    if dtstart:
                        journal_data["date"] = dtstart.dt.strftime("%m/%d/%Y %H:%M")

                    journal_data["status"] = str(component.get("status", ""))
                    break  # We only need the first VJOURNAL

            logger.info(f"Read journal: {journal_id}")
            return journal_data
        except Exception as e:
            logger.error(f"Failed to read journal: {e}")
            raise  # Propagate the exception

    def update_journal(self, journal_id: str, journal_data: Dict[str, Any]) -> bool:
        """
        Update an existing journal entry in the CalDAV server.

        Args:
            journal_id: ID of the journal entry to update
            journal_data: Dictionary containing updated journal data

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the journal by ID
            journal = calendar.journal(journal_id)

            # Update the journal properties by modifying the icalendar instance
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
                    break  # We only need to modify the first VJOURNAL

            # Save the updated journal
            journal.save()

            logger.info(f"Updated journal: {journal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update journal: {e}")
            raise  # Propagate the exception

    def delete_journal(self, journal_id: str) -> bool:
        """
        Delete a journal entry from the CalDAV server.

        Args:
            journal_id: ID of the journal entry to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the journal by ID
            journal = calendar.journal(journal_id)

            # Delete the journal
            journal.delete()

            logger.info(f"Deleted journal: {journal_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete journal: {e}")
            raise  # Propagate the exception

    def create_todo(self, todo: Todo) -> Optional[str]:
        """Create a new todo item in the CalDAV server using a Todo object.
    
        Args:
            todo: A :class:`~models.todo.Todo` instance containing the todo data.
    
        Returns:
            The ID of the created todo or ``None`` if creation failed.
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")
    
        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar
    
            # Create todo using calendar.save_todo with parameters from the Todo object
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

    def read_todo(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a todo item from the CalDAV server.

        Args:
            todo_id: ID of the todo item to read

        Returns:
            Dictionary containing todo data or None if not found
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the todo by ID
            todo = calendar.todo(todo_id)

            # Convert to dictionary format
            todo_data = {
                "id": todo_id,
                "title": "",
                "description": "",
                "priority": 5,
                "status": "",
                "due_date": "",
                "completed_date": "",
            }

            # Walk through components to find VTODO
            for component in todo.icalendar_instance.walk():
                if component.name == "VTODO":
                    todo_data["title"] = str(component.get("summary", ""))
                    todo_data["description"] = str(component.get("description", ""))

                    # Handle priority
                    priority = component.get("priority")
                    if priority:
                        todo_data["priority"] = int(priority)

                    todo_data["status"] = str(component.get("status", ""))

                    # Handle date/time values
                    due = component.get("due")
                    if due:
                        todo_data["due_date"] = due.dt.strftime("%m/%d/%Y %H:%M")

                    completed = component.get("completed")
                    if completed:
                        todo_data["completed_date"] = completed.dt.strftime(
                            "%m/%d/%Y %H:%M"
                        )
                    break  # We only need the first VTODO

            logger.info(f"Read todo: {todo_id}")
            return todo_data
        except Exception as e:
            logger.error(f"Failed to read todo: {e}")
            raise  # Propagate the exception

    def update_todo(self, todo_id: str, todo_data: Dict[str, Any]) -> bool:
        """
        Update an existing todo item in the CalDAV server.

        Args:
            todo_id: ID of the todo item to update
            todo_data: Dictionary containing updated todo data

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the todo by ID
            todo = calendar.todo(todo_id)

            # Update the todo properties by modifying the icalendar instance
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
                    break  # We only need to modify the first VTODO

            # Save the updated todo
            todo.save()

            logger.info(f"Updated todo: {todo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update todo: {e}")
            raise  # Propagate the exception

    def delete_todo(self, todo_id: str) -> bool:
        """
        Delete a todo item from the CalDAV server.

        Args:
            todo_id: ID of the todo item to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Retrieve the todo by ID
            todo = calendar.todo(todo_id)

            # Delete the todo
            todo.delete()

            logger.info(f"Deleted todo: {todo_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete todo: {e}")
            raise  # Propagate the exception

    def _convert_caldav_event(self, caldav_event) -> Event:
        """
        Convert a CalDAV event to an Event object.

        Args:
            caldav_event: CalDAV event object

        Returns:
            Event object
        """
        # Extract event properties by walking through components
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

        # Walk through components to find VEVENT
        for component in caldav_event.icalendar_instance.walk():
            if component.name == "VEVENT":
                event_data["title"] = str(component.get("summary", ""))
                event_data["description"] = str(component.get("description", ""))

                # Handle date/time values
                dtstart = component.get("dtstart")
                if dtstart:
                    event_data["start_time"] = dtstart.dt

                dtend = component.get("dtend")
                if dtend:
                    event_data["end_time"] = dtend.dt

                event_data["location"] = str(component.get("location", ""))
                event_data["status"] = str(component.get("status", ""))

                # Handle attendees
                attendees = component.get("attendee", [])
                if attendees:
                    if isinstance(attendees, list):
                        event_data["attendees"] = [str(a) for a in attendees]
                    else:
                        event_data["attendees"] = [str(attendees)]

                # Handle recurrence rule
                rrule = component.get("rrule")
                if rrule:
                    event_data["rrule"] = rrule

                # Ensure ID is set from UID if missing
                if not event_data["id"]:
                    uid = component.get("uid")
                    if uid:
                        event_data["id"] = str(uid)

                break  # We only need the first VEVENT

        # Create Event object from the extracted data
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
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list:
        """
        Retrieve events from the CalDAV server.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            List of Event objects or empty list if failed
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Fetch events from the calendar
            if start_date and end_date:
                # Filter by date range
                events = calendar.events(start=start_date, end=end_date)
            else:
                # Get all events
                events = calendar.events()

            # Convert events to list of Event objects
            event_list = []
            for event in events:
                event_list.append(self._convert_caldav_event(event))

            logger.info(f"Retrieved {len(event_list)} events")
            return event_list

        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            raise  # Propagate the exception

    def get_todos(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list:
        """
        Retrieve todos from the CalDAV server.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            List of Todo objects or empty list if failed
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Fetch todos from the calendar
            if start_date and end_date:
                # Filter by date range
                todos = calendar.todos(start=start_date, end=end_date)
            else:
                # Get all todos
                todos = calendar.todos()

            # Convert todos to list of Todo objects
            todo_list = []
            for todo in todos:
                # Extract todo properties by walking through components
                todo_data = {
                    "id": todo.id,
                    "title": "",
                    "description": "",
                    "priority": 5,
                    "status": "",
                    "due_date": None,
                    "completion_date": None,
                }

                # Walk through components to find VTODO
                for component in todo.icalendar_instance.walk():
                    if component.name == "VTODO":
                        todo_data["title"] = str(component.get("summary", ""))
                        todo_data["description"] = str(component.get("description", ""))

                        # Handle priority
                        priority = component.get("priority")
                        if priority:
                            todo_data["priority"] = int(priority)

                        todo_data["status"] = str(component.get("status", ""))

                        # Handle date/time values
                        due = component.get("due")
                        if due:
                            todo_data["due_date"] = due.dt

                        completed = component.get("completed")
                        if completed:
                            todo_data["completion_date"] = completed.dt
                        # Fallback to UID if ID not set
                        if not todo_data["id"]:
                            uid = component.get("uid")
                            if uid:
                                todo_data["id"] = str(uid)
                        break  # We only need the first VTODO

                # Create Todo object from the extracted data
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
            raise  # Propagate the exception
    
    def get_journals(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> list:
        """
        Retrieve journals from the CalDAV server.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Returns:
            List of journal dictionaries or empty list if failed
        """
        if not self.connected:
            logger.error("Not connected to the calendar")
            raise Exception("Not connected to the calendar")

        try:
            # Get the principal and calendar
            principal = self.client.principal()
            calendar = principal.calendars()[0]  # Use first calendar

            # Fetch journals from the calendar
            if start_date and end_date:
                journals = calendar.journals(start=start_date, end=end_date)
            else:
                journals = calendar.journals()

            journal_list = []
            for journal in journals:
                # Use existing read_journal to get dict representation
                journal_data = self.read_journal(journal.id)
                journal_list.append(journal_data)

            logger.info(f"Retrieved {len(journal_list)} journals")
            return journal_list
        except Exception as e:
            logger.error(f"Failed to retrieve journals: {e}")
            raise  # Propagate the exception
