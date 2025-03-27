"""
External Integrations Example

This script demonstrates how to integrate MCP with external services by creating
custom tools that connect to:
1. Weather API service
2. Database service
3. File storage service
4. Email notification service
5. SMS/messaging service

Note: This is a demonstration that uses mock APIs rather than real service calls.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from mcp_example.core.executor import executor
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition, PropertySchema
from mcp_example.tools import register_all_tools

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Mock external service responses
MOCK_WEATHER_DATA = {
    "New York": {
        "temperature": 72,
        "condition": "Partly Cloudy",
        "humidity": 65,
        "wind_speed": 8
    },
    "London": {
        "temperature": 62,
        "condition": "Rainy",
        "humidity": 85,
        "wind_speed": 12
    },
    "Tokyo": {
        "temperature": 81,
        "condition": "Sunny",
        "humidity": 70,
        "wind_speed": 5
    },
    "Sydney": {
        "temperature": 68,
        "condition": "Clear",
        "humidity": 45,
        "wind_speed": 10
    }
}

MOCK_DATABASE = {
    "users": [
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "status": "active"},
        {"id": 2, "name": "Bob Jones", "email": "bob@example.com", "status": "inactive"},
        {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "status": "active"}
    ],
    "products": [
        {"id": 101, "name": "Laptop", "price": 999.99, "in_stock": True},
        {"id": 102, "name": "Smartphone", "price": 499.99, "in_stock": True},
        {"id": 103, "name": "Headphones", "price": 99.99, "in_stock": False}
    ],
    "orders": [
        {"id": 1001, "user_id": 1, "products": [101, 103], "total": 1099.98, "status": "shipped"},
        {"id": 1002, "user_id": 3, "products": [102], "total": 499.99, "status": "processing"}
    ]
}

MOCK_FILE_STORAGE = {}

MOCK_EMAIL_SENT = []

MOCK_SMS_SENT = []


# Weather API Tool
def register_weather_tool() -> None:
    """Register a tool for retrieving weather data from an external service."""
    def get_weather(city: str, units: str = "imperial") -> Dict[str, Any]:
        """
        Get current weather for a city (mock implementation).
        
        Args:
            city: Name of the city
            units: Temperature units (imperial or metric)
            
        Returns:
            Weather data for the specified city
        """
        logger.info(f"Retrieving weather data for {city} in {units} units")
        
        # Simulate API call delay
        time.sleep(0.5)
        
        if city not in MOCK_WEATHER_DATA:
            raise ValueError(f"City {city} not found in weather database")
        
        weather = MOCK_WEATHER_DATA[city].copy()
        
        # Convert temperature if needed
        if units == "metric" and "temperature" in weather:
            # Convert Fahrenheit to Celsius
            weather["temperature"] = round((weather["temperature"] - 32) * 5/9, 1)
        
        weather["city"] = city
        weather["units"] = units
        weather["timestamp"] = datetime.now().isoformat()
        
        return weather
    
    # Register the function
    registry.register_tool(
        name="weather",
        function=get_weather,
        description="Get current weather for a city",
        schema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Name of the city"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units",
                    "enum": ["imperial", "metric"],
                    "default": "imperial"
                }
            },
            "required": ["city"]
        }
    )


# Database Tool
def register_database_tool() -> None:
    """Register a tool for interacting with a database."""
    def query_database(table: str, filter_field: Optional[str] = None, 
                      filter_value: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Query a database table with optional filtering (mock implementation).
        
        Args:
            table: Name of the table to query
            filter_field: Optional field to filter on
            filter_value: Value to match for filtering
            
        Returns:
            List of matching records
        """
        logger.info(f"Querying {table} table with filter {filter_field}={filter_value}")
        
        # Simulate database query delay
        time.sleep(0.7)
        
        if table not in MOCK_DATABASE:
            raise ValueError(f"Table {table} not found in database")
        
        records = MOCK_DATABASE[table]
        
        # Apply filter if provided
        if filter_field and filter_value is not None:
            filtered_records = []
            for record in records:
                if filter_field in record and record[filter_field] == filter_value:
                    filtered_records.append(record)
            records = filtered_records
        
        return records
    
    # Register the function
    registry.register_tool(
        name="database_query",
        function=query_database,
        description="Query a database table with optional filtering",
        schema={
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "Name of the table to query",
                    "enum": ["users", "products", "orders"]
                },
                "filter_field": {
                    "type": "string",
                    "description": "Field to filter on (optional)"
                },
                "filter_value": {
                    "description": "Value to match for filtering (optional)"
                }
            },
            "required": ["table"]
        }
    )


# File Storage Tool
def register_file_storage_tool() -> None:
    """Register a tool for interacting with a file storage service."""
    def store_file(filename: str, content: str, folder: str = "default") -> Dict[str, Any]:
        """
        Store a file in the cloud storage (mock implementation).
        
        Args:
            filename: Name of the file
            content: File content
            folder: Folder to store the file in
            
        Returns:
            File metadata
        """
        logger.info(f"Storing file {filename} in folder {folder}")
        
        # Simulate storage API call delay
        time.sleep(1.0)
        
        # Create folder if it doesn't exist
        if folder not in MOCK_FILE_STORAGE:
            MOCK_FILE_STORAGE[folder] = {}
        
        # Store the file
        file_id = f"{int(time.time())}-{filename}"
        MOCK_FILE_STORAGE[folder][filename] = {
            "id": file_id,
            "content": content,
            "size": len(content),
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "id": file_id,
            "filename": filename,
            "folder": folder,
            "size": len(content),
            "url": f"https://example.com/files/{folder}/{filename}",
            "created_at": datetime.now().isoformat()
        }
    
    def retrieve_file(filename: str, folder: str = "default") -> Dict[str, Any]:
        """
        Retrieve a file from cloud storage (mock implementation).
        
        Args:
            filename: Name of the file
            folder: Folder where the file is stored
            
        Returns:
            File metadata and content
        """
        logger.info(f"Retrieving file {filename} from folder {folder}")
        
        # Simulate retrieval API call delay
        time.sleep(0.8)
        
        if folder not in MOCK_FILE_STORAGE or filename not in MOCK_FILE_STORAGE[folder]:
            raise ValueError(f"File {filename} not found in folder {folder}")
        
        file_data = MOCK_FILE_STORAGE[folder][filename]
        
        return {
            "id": file_data["id"],
            "filename": filename,
            "folder": folder,
            "content": file_data["content"],
            "size": file_data["size"],
            "url": f"https://example.com/files/{folder}/{filename}",
            "created_at": file_data["created_at"]
        }
    
    # Register the functions
    registry.register_tool(
        name="store_file",
        function=store_file,
        description="Store a file in cloud storage",
        schema={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the file"
                },
                "content": {
                    "type": "string",
                    "description": "File content"
                },
                "folder": {
                    "type": "string",
                    "description": "Folder to store the file in",
                    "default": "default"
                }
            },
            "required": ["filename", "content"]
        }
    )
    
    registry.register_tool(
        name="retrieve_file",
        function=retrieve_file,
        description="Retrieve a file from cloud storage",
        schema={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the file"
                },
                "folder": {
                    "type": "string",
                    "description": "Folder where the file is stored",
                    "default": "default"
                }
            },
            "required": ["filename"]
        }
    )


# Email Notification Tool
def register_email_tool() -> None:
    """Register a tool for sending email notifications."""
    def send_email(to: Union[str, List[str]], subject: str, body: str, 
                  cc: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send an email notification (mock implementation).
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body
            cc: Carbon copy recipient(s)
            
        Returns:
            Email delivery status
        """
        logger.info(f"Sending email to {to} with subject '{subject}'")
        
        # Simulate email API call delay
        time.sleep(1.2)
        
        # Normalize recipient format
        if isinstance(to, str):
            recipients = [to]
        else:
            recipients = to
        
        # Create email payload
        email = {
            "to": recipients,
            "subject": subject,
            "body": body,
            "cc": cc or [],
            "sent_at": datetime.now().isoformat(),
            "message_id": f"email-{len(MOCK_EMAIL_SENT) + 1}-{int(time.time())}"
        }
        
        # Store in sent emails
        MOCK_EMAIL_SENT.append(email)
        
        return {
            "success": True,
            "message_id": email["message_id"],
            "recipients": len(recipients) + len(email["cc"]),
            "sent_at": email["sent_at"]
        }
    
    # Register the function
    registry.register_tool(
        name="send_email",
        function=send_email,
        description="Send an email notification",
        schema={
            "type": "object",
            "properties": {
                "to": {
                    "description": "Recipient email address(es)",
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}}
                    ]
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body"
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Carbon copy recipient(s)"
                }
            },
            "required": ["to", "subject", "body"]
        }
    )


# SMS/Messaging Tool
def register_sms_tool() -> None:
    """Register a tool for sending SMS messages."""
    def send_sms(to: str, message: str) -> Dict[str, Any]:
        """
        Send an SMS message (mock implementation).
        
        Args:
            to: Recipient phone number
            message: Message content
            
        Returns:
            SMS delivery status
        """
        logger.info(f"Sending SMS to {to}")
        
        # Simulate SMS API call delay
        time.sleep(0.9)
        
        # Validate phone number format (simple check)
        if not (to.startswith("+") and len(to) >= 10):
            raise ValueError(f"Invalid phone number format: {to}. Must start with + and have at least 10 digits.")
        
        # Create SMS payload
        sms = {
            "to": to,
            "message": message,
            "sent_at": datetime.now().isoformat(),
            "message_id": f"sms-{len(MOCK_SMS_SENT) + 1}-{int(time.time())}"
        }
        
        # Store in sent messages
        MOCK_SMS_SENT.append(sms)
        
        return {
            "success": True,
            "message_id": sms["message_id"],
            "sent_at": sms["sent_at"],
            "segments": max(1, len(message) // 160)  # SMS segments calculation
        }
    
    # Register the function
    registry.register_tool(
        name="send_sms",
        function=send_sms,
        description="Send an SMS message",
        schema={
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient phone number (E.164 format starting with +)"
                },
                "message": {
                    "type": "string",
                    "description": "Message content"
                }
            },
            "required": ["to", "message"]
        }
    )


def register_all_external_tools() -> None:
    """Register all external integration tools."""
    register_weather_tool()
    register_database_tool()
    register_file_storage_tool()
    register_email_tool()
    register_sms_tool()


def demonstrate_weather_tool() -> None:
    """Demonstrate the weather tool."""
    print("=== Weather API Integration Example ===")
    
    # Get weather for New York in imperial units
    ny_weather = executor.execute_function({
        "name": "weather",
        "parameters": {
            "city": "New York",
            "units": "imperial"
        }
    })
    
    print(f"New York Weather (imperial): {json.dumps(ny_weather.result, indent=2)}")
    
    # Get weather for London in metric units
    london_weather = executor.execute_function({
        "name": "weather",
        "parameters": {
            "city": "London",
            "units": "metric"
        }
    })
    
    print(f"London Weather (metric): {json.dumps(london_weather.result, indent=2)}")
    
    # Handle error case
    try:
        unknown_weather = executor.execute_function({
            "name": "weather",
            "parameters": {
                "city": "Unknown City"
            }
        })
    except Exception as e:
        print(f"Expected error: {str(e)}")


def demonstrate_database_tool() -> None:
    """Demonstrate the database tool."""
    print("\n=== Database Integration Example ===")
    
    # Query all users
    all_users = executor.execute_function({
        "name": "database_query",
        "parameters": {
            "table": "users"
        }
    })
    
    print(f"All users: {json.dumps(all_users.result, indent=2)}")
    
    # Query active users
    active_users = executor.execute_function({
        "name": "database_query",
        "parameters": {
            "table": "users",
            "filter_field": "status",
            "filter_value": "active"
        }
    })
    
    print(f"Active users: {json.dumps(active_users.result, indent=2)}")
    
    # Query products in stock
    in_stock = executor.execute_function({
        "name": "database_query",
        "parameters": {
            "table": "products",
            "filter_field": "in_stock",
            "filter_value": True
        }
    })
    
    print(f"Products in stock: {json.dumps(in_stock.result, indent=2)}")


def demonstrate_file_storage_tool() -> None:
    """Demonstrate the file storage tool."""
    print("\n=== File Storage Integration Example ===")
    
    # Store a file
    file_metadata = executor.execute_function({
        "name": "store_file",
        "parameters": {
            "filename": "report.txt",
            "content": "This is a sample report with important information.",
            "folder": "reports"
        }
    })
    
    print(f"Stored file metadata: {json.dumps(file_metadata.result, indent=2)}")
    
    # Store another file
    file_metadata2 = executor.execute_function({
        "name": "store_file",
        "parameters": {
            "filename": "config.json",
            "content": '{"debug": true, "logLevel": "info"}',
            "folder": "configs"
        }
    })
    
    print(f"Stored file metadata: {json.dumps(file_metadata2.result, indent=2)}")
    
    # Retrieve a file
    retrieved_file = executor.execute_function({
        "name": "retrieve_file",
        "parameters": {
            "filename": "report.txt",
            "folder": "reports"
        }
    })
    
    print(f"Retrieved file: {json.dumps(retrieved_file.result, indent=2)}")


def demonstrate_notification_tools() -> None:
    """Demonstrate the email and SMS notification tools."""
    print("\n=== Notification Integration Example ===")
    
    # Send email
    email_result = executor.execute_function({
        "name": "send_email",
        "parameters": {
            "to": ["user@example.com", "admin@example.com"],
            "subject": "Important Notification",
            "body": "This is an important notification about your account.",
            "cc": ["manager@example.com"]
        }
    })
    
    print(f"Email result: {json.dumps(email_result.result, indent=2)}")
    
    # Send SMS
    sms_result = executor.execute_function({
        "name": "send_sms",
        "parameters": {
            "to": "+12345678901",
            "message": "Your verification code is 123456"
        }
    })
    
    print(f"SMS result: {json.dumps(sms_result.result, indent=2)}")


def demonstrate_complex_workflow() -> None:
    """Demonstrate a complex workflow using multiple external integrations."""
    print("\n=== Complex Integration Workflow Example ===")
    
    # Step 1: Query database for active users
    active_users = executor.execute_function({
        "name": "database_query",
        "parameters": {
            "table": "users",
            "filter_field": "status",
            "filter_value": "active"
        }
    }).result
    
    print(f"Found {len(active_users)} active users")
    
    # Step 2: Get weather for a city
    weather = executor.execute_function({
        "name": "weather",
        "parameters": {
            "city": "New York",
            "units": "metric"
        }
    }).result
    
    print(f"Current weather in {weather['city']}: {weather['condition']}, {weather['temperature']}°C")
    
    # Step 3: Create a report with the combined data
    report_content = f"""
Weather and User Report
Generated: {datetime.now().isoformat()}

Weather Information:
City: {weather['city']}
Condition: {weather['condition']}
Temperature: {weather['temperature']}°C
Humidity: {weather['humidity']}%
Wind Speed: {weather['wind_speed']} mph

Active Users ({len(active_users)}):
"""
    
    for user in active_users:
        report_content += f"- {user['name']} ({user['email']})\n"
    
    # Step 4: Store the report
    report_metadata = executor.execute_function({
        "name": "store_file",
        "parameters": {
            "filename": "combined_report.txt",
            "content": report_content,
            "folder": "reports"
        }
    }).result
    
    print(f"Generated report: {report_metadata['url']}")
    
    # Step 5: Send email notification about the report
    email_result = executor.execute_function({
        "name": "send_email",
        "parameters": {
            "to": [user["email"] for user in active_users],
            "subject": f"Weather Report for {weather['city']}",
            "body": f"Hello,\n\nA new weather report is available. "
                   f"The current temperature in {weather['city']} is {weather['temperature']}°C "
                   f"with {weather['condition']} conditions.\n\n"
                   f"View the full report at: {report_metadata['url']}\n\n"
                   f"Thanks,\nThe System"
        }
    }).result
    
    print(f"Notification sent to {email_result['recipients']} users")


def main() -> None:
    """Main function to run the examples."""
    # Register standard and external tools
    register_all_tools()
    register_all_external_tools()
    
    # Demonstrate individual tools
    demonstrate_weather_tool()
    demonstrate_database_tool()
    demonstrate_file_storage_tool()
    demonstrate_notification_tools()
    
    # Demonstrate complex workflow
    demonstrate_complex_workflow()


if __name__ == "__main__":
    main() 