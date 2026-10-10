"""
Feed Form - Main application logic
Offline-first data entry for feed type and weight
"""

import json
from datetime import datetime
from js import document, localStorage
from pyodide.ffi import create_proxy

# =============================================================================
# GLOBAL STATE
# =============================================================================

STORAGE_KEY = "feed_form_records"
RECORDS = []


# =============================================================================
# DATA STORAGE
# =============================================================================

def load_records():
    """Load records from browser localStorage"""
    global RECORDS
    try:
        stored = localStorage.getItem(STORAGE_KEY)
        if stored:
            RECORDS = json.loads(stored)
        else:
            RECORDS = []
    except Exception as e:
        print(f"Error loading records: {e}")
        RECORDS = []
    return RECORDS


def save_records():
    """Save records to browser localStorage"""
    try:
        localStorage.setItem(STORAGE_KEY, json.dumps(RECORDS))
        return True
    except Exception as e:
        print(f"Error saving records: {e}")
        return False


def add_record(record):
    """Add a new record to the storage"""
    global RECORDS
    load_records()
    RECORDS.append(record)
    save_records()
    update_record_count()
    return record


def clear_all_records():
    """Clear all stored records"""
    global RECORDS
    try:
        localStorage.removeItem(STORAGE_KEY)
        RECORDS = []
        update_record_count()
        show_status("All records cleared", "success")
        return True
    except Exception as e:
        print(f"Error clearing records: {e}")
        show_status(f"Error: {e}", "error")
        return False


def update_record_count():
    """Update the displayed record count"""
    load_records()
    count_element = document.getElementById("record-count")
    if count_element:
        count_element.innerText = str(len(RECORDS))


# =============================================================================
# UI HELPERS
# =============================================================================

def show_status(message, status_type="info"):
    """Show a status message in the status bar"""
    status_bar = document.getElementById("status-bar")
    if status_bar:
        status_bar.innerText = message
        status_bar.className = f"status-bar {status_type} show"
        
        # Hide after 3 seconds
        def hide_status():
            if status_bar:
                status_bar.className = f"status-bar {status_type}"
        
        # Use setTimeout via js
        from js import setTimeout
        setTimeout(create_proxy(hide_status), 3000)


# =============================================================================
# FORM DATA HANDLING
# =============================================================================

def get_form_data():
    """Extract form data from the HTML form"""
    record = {
        "timestamp": document.getElementById("timestamp").value,
        "material": document.getElementById("material").value,
        "weight": document.getElementById("weight").value,
        "notes": document.getElementById("notes").value
    }
    return record


def validate_form():
    """Validate form inputs"""
    material = document.getElementById("material").value
    weight = document.getElementById("weight").value
    timestamp = document.getElementById("timestamp").value
    
    if not material:
        show_status("Please select a feed type", "error")
        return False
    
    if not weight:
        show_status("Please enter a weight", "error")
        return False
    
    if not timestamp:
        show_status("Please enter a timestamp", "error")
        return False
    
    return True


def clear_form():
    """Clear the form fields"""
    document.getElementById("timestamp").value = datetime.now().strftime("%Y-%m-%dT%H:%M")
    document.getElementById("material").value = ""
    document.getElementById("weight").value = ""
    document.getElementById("notes").value = ""
    show_status("Form cleared", "success")


# =============================================================================
# CSV EXPORT
# =============================================================================

def generate_csv():
    """Generate CSV data from stored records"""
    load_records()
    
    if not RECORDS:
        show_status("No records to export", "error")
        return None
    
    # Build CSV content
    csv_lines = ["timestamp,material,weight,notes"]
    for record in RECORDS:
        timestamp = record.get("timestamp", "")
        material = record.get("material", "")
        weight = record.get("weight", "")
        notes = record.get("notes", "")
        
        # Escape values if needed
        def escape_csv(value):
            value = str(value) if value else ""
            return value
        
        csv_lines.append(f"{escape_csv(timestamp)},{escape_csv(material)},{escape_csv(weight)},{escape_csv(notes)}")
    
    return "\n".join(csv_lines)


def trigger_download(csv_data):
    """Trigger a file download in the browser"""
    from js import Blob, URL, document
    blob = Blob.new([csv_data], {"type": "text/csv"})
    url = URL.createObjectURL(blob)
    
    a = document.createElement("a")
    a.href = url
    a.download = "feed_form_export.csv"
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)


def export_csv(event=None):
    """Export records as CSV file"""
    csv_data = generate_csv()
    if csv_data:
        trigger_download(csv_data)
        show_status(f"Exported {len(RECORDS)} records", "success")


# =============================================================================
# EVENT HANDLERS
# =============================================================================

def save_entry(event=None):
    """Save the current form entry"""
    if not validate_form():
        return
    
    record = get_form_data()
    add_record(record)
    clear_form()
    show_status("Entry saved", "success")


def confirm_clear_all(event=None):
    """Confirm and clear all records"""
    from js import confirm
    result = confirm("Are you sure you want to clear ALL records? This cannot be undone.")
    if result:
        clear_all_records()


# =============================================================================
# INITIALIZATION
# =============================================================================

def init():
    """Initialize the application"""
    load_records()
    
    # Set current timestamp
    timestamp_element = document.getElementById("timestamp")
    if timestamp_element:
        timestamp_element.value = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    # Set up event handlers using PyScript's Element API
    save_btn = document.getElementById("save-btn")
    if save_btn:
        save_btn.addEventListener("click", create_proxy(save_entry))
    
    clear_btn = document.getElementById("clear-btn")
    if clear_btn:
        clear_btn.addEventListener("click", create_proxy(clear_form))
    
    export_btn = document.getElementById("export-btn")
    if export_btn:
        export_btn.addEventListener("click", create_proxy(export_csv))
    
    clear_all_btn = document.getElementById("clear-all-btn")
    if clear_all_btn:
        clear_all_btn.addEventListener("click", create_proxy(confirm_clear_all))
    
    update_record_count()
    show_status("Feed Form ready", "success")


# Initialize when the script loads
init()
