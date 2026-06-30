"""
Todo Model for MCP CalDAV Application
Represents todo items with all relevant properties.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from models.base_model import BaseModel


class Todo(BaseModel):
    """Model representing a todo item."""

    def __init__(
        self,
        title: str = "",
        description: str = "",
        due_date: datetime = None,
        completion_date: datetime = None,
        status: str = "NEEDS-ACTION",
        priority: int = 5,
        categories: List[str] = None,
        url: str = "",
        percent_complete: int = 0,
        calendar_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a Todo model.

        Args:
            title: Todo title
            description: Todo description
            due_date: Due date for the todo
            completion_date: Date when the todo was completed
            status: Todo status (NEEDS-ACTION, COMPLETED, IN-PROCESS, CANCELLED)
            priority: Priority level (1-9)
            categories: List of categories/tags
            url: URL associated with the todo
            percent_complete: Percentage of completion (0-100)
            **kwargs: Additional properties
        """
        super().__init__(**kwargs)

        self.title = title
        self.description = description
        self.due_date = due_date
        self.completion_date = completion_date
        self.status = status
        self.priority = priority
        self.categories = categories or []
        self.url = url
        self.percent_complete = percent_complete
        self.calendar_name = calendar_name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert todo to dictionary representation.

        Returns:
            Dictionary representation of the todo item
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "completion_date": self.completion_date,
            "status": self.status,
            "priority": self.priority,
            "categories": self.categories,
            "url": self.url,
            "percent_complete": self.percent_complete,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Initialize todo from dictionary data.

        Args:
            data: Dictionary containing todo data
        """
        self.id = data.get("id", self.id)
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.status = data.get("status", "NEEDS-ACTION")
        self.priority = data.get("priority", 5)
        self.categories = data.get("categories", [])
        self.url = data.get("url", "")
        self.percent_complete = data.get("percent_complete", 0)

        # Handle datetime conversion
        due_date_str = data.get("due_date")
        if due_date_str:
            self.due_date = datetime.fromisoformat(due_date_str)
        else:
            self.due_date = None

        completion_date_str = data.get("completion_date")
        if completion_date_str:
            self.completion_date = datetime.fromisoformat(completion_date_str)
        else:
            self.completion_date = None

    def to_ical(self) -> str:
        """
        Convert todo to iCalendar format.

        Returns:
            iCalendar string representation
        """
        # This is a simplified implementation
        # In a real implementation, this would use the caldav library properly
        ical = "BEGIN:VTODO\n"
        ical += f"UID:{self.id}\n"
        ical += f"SUMMARY:{self.title}\n"
        ical += f"DESCRIPTION:{self.description}\n"
        if self.due_date:
            ical += f"DUE:{self.due_date.strftime('%Y%m%dT%H%M%S')}\n"
        if self.completion_date:
            ical += f"COMPLETED:{self.completion_date.strftime('%Y%m%dT%H%M%S')}\n"
        ical += f"STATUS:{self.status}\n"
        ical += f"PRIORITY:{self.priority}\n"
        ical += f"PERCENT-COMPLETE:{self.percent_complete}\n"
        if self.url:
            ical += f"URL:{self.url}\n"
        ical += "END:VTODO\n"
        return ical

    def from_ical(self, ical_str: str) -> None:
        """
        Initialize todo from iCalendar string.

        Args:
            ical_str: iCalendar string representation
        """
        # This is a simplified implementation
        # In a real implementation, this would parse the iCalendar properly
        pass

    def validate(self) -> bool:
        """
        Validate the todo data.

        Returns:
            True if valid, False otherwise
        """
        if not self.title:
            return False
        if self.priority < 1 or self.priority > 9:
            return False
        if self.percent_complete < 0 or self.percent_complete > 100:
            return False
        return True
