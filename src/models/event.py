"""
Event Model for MCP CalDAV Application
Represents calendar events with all relevant properties.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from models.base_model import BaseModel


class Event(BaseModel):
    """Model representing a calendar event."""

    def __init__(
        self,
        title: str = "",
        description: str = "",
        start_time: datetime = None,
        end_time: datetime = None,
        location: str = "",
        attendees: List[str] = None,
        categories: List[str] = None,
        status: str = "CONFIRMED",
        priority: int = 5,
        url: str = "",
        vevent: Any = None,
        rrule: Any = None,
        calendar_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize an Event model.

        Args:
            title: Event title
            description: Event description
            start_time: Event start time
            end_time: Event end time
            location: Event location
            attendees: List of attendee email addresses
            categories: List of categories/tags
            status: Event status (CONFIRMED, TENTATIVE, CANCELLED)
            priority: Priority level (1-9)
            url: URL associated with the event
            **kwargs: Additional properties
        """
        super().__init__(**kwargs)

        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.attendees = attendees or []
        self.categories = categories or []
        self.status = status
        self.priority = priority
        self.url = url
        self.vevent = vevent
        self.rrule = rrule
        self.calendar_name = calendar_name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary representation.

        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "attendees": self.attendees,
            "categories": self.categories,
            "status": self.status,
            "priority": self.priority,
            "url": self.url,
            "rrule": self.rrule,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Initialize event from dictionary data.

        Args:
            data: Dictionary containing event data
        """
        self.id = data.get("id", self.id)
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.location = data.get("location", "")
        self.attendees = data.get("attendees", [])
        self.categories = data.get("categories", [])
        self.status = data.get("status", "CONFIRMED")
        self.priority = data.get("priority", 5)
        self.url = data.get("url", "")
        self.vevent = data.get("vevent", None)
        self.rrule = data.get("rrule", None)

        # Handle datetime conversion
        start_time_str = data.get("start_time")
        if start_time_str:
            self.start_time = datetime.fromisoformat(start_time_str)
        else:
            self.start_time = None

        end_time_str = data.get("end_time")
        if end_time_str:
            self.end_time = datetime.fromisoformat(end_time_str)
        else:
            self.end_time = None

    def to_ical(self) -> str:
        """
        Convert event to iCalendar format.

        Returns:
            iCalendar string representation
        """
        # This is a simplified implementation
        # In a real implementation, this would use the caldav library properly
        ical = "BEGIN:VEVENT\n"
        ical += f"UID:{self.id}\n"
        ical += f"SUMMARY:{self.title}\n"
        ical += f"DESCRIPTION:{self.description}\n"
        if self.start_time:
            ical += f"DTSTART:{self.start_time.strftime('%Y%m%dT%H%M%S')}\n"
        if self.end_time:
            ical += f"DTEND:{self.end_time.strftime('%Y%m%dT%H%M%S')}\n"
        ical += f"LOCATION:{self.location}\n"
        ical += f"STATUS:{self.status}\n"
        ical += f"PRIORITY:{self.priority}\n"
        if self.url:
            ical += f"URL:{self.url}\n"
        ical += "END:VEVENT\n"
        return ical

    def from_ical(self, ical_str: str) -> None:
        """
        Initialize event from iCalendar string.

        Args:
            ical_str: iCalendar string representation
        """
        # This is a simplified implementation
        # In a real implementation, this would parse the iCalendar properly
        pass

    def validate(self) -> bool:
        """
        Validate the event data.

        Returns:
            True if valid, False otherwise
        """
        if not self.title:
            return False
        if self.priority < 1 or self.priority > 9:
            return False
        return True
