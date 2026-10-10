"""
Feed Form - Main application logic
Offline-first data entry for feed type and weight
"""

import json
import js
from datetime import datetime

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
        stored = js.localStorage.getItem(STORAGE_KEY)
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
        js.localStorage.setItem(STORAGE_KEY, json.dumps(RECORDS))
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
        js.localStorage.removeItem(STORAGE_KEY)
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
    count_element = js.document.getElementById("record-count")
    if count_element:
        count_element.innerText = str(len(RECORDS))


# =============================================================================
# UI HELPERS
# =============================================================================

def show_status(message, status_type="info"):
    """Show a status message in the status bar"""
    status_bar = js.document.getElementById("status-bar")
    if status_bar:
        status_bar.innerText = message
        status_bar.className = f"status-bar {status_type} show"
        
        # Hide after 3 seconds
        def hide_status():
            if status_bar:
                status_bar.className = f"status-bar {status_type}"
        
        js.setTimeout(hide_status, 3000)


# =============================================================================
# FORM DATA HANDLING
# =============================================================================

def get_form_data():
    """Extract form data from the HTML form"""
    record = {
        "timestamp": js.document.getElementById("timestamp").value,
        "material": js.document.getElementById("material").value,
        "weight": js.document.getElementById("weight").value,
        "notes": js.document.getElementById("notes").value
    }
    return record


def validate_form():
    """Validate form inputs"""
    material = js.document.getElementById("material").value
    weight = js.document.getElementById("weight").value
    timestamp = js.document.getElementById("timestamp").value
    
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
    js.document.getElementById("timestamp").value = datetime.now().strftime("%Y-%m-%dT%H:%M")
    js.document.getElementById("material").value = ""
    js.document.getElementById("weight").value = ""
    js.document.getElementById("notes").value = ""
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
            if "," in value or '"' in value or "\n" in value:
                value = f'"{value.replace("\"", "\\\""} }"'
            return value
        
        csv_lines.append(f"{escape_csv(timestamp)},{escape_csv(material)},{escape_csv(weight)},{escape_csv(notes)}")
    
    return "\n".join(csv_lines)


def trigger_download(csv_data):
    """Trigger a file download in the browser"""
    blob = js.Blob.new([csv_data], {"type": "text/csv"})
    url = js.URL.createObjectURL(blob)
    
    a = js.document.createElement("a")
    a.href = url
    a.download = "feed_form_export.csv"
    js.document.body.appendChild(a)
    a.click()
    js.document.body.removeChild(a)
    js.URL.revokeObjectURL(url)


def export_csv(event=None):
    """Export records as CSV file"""
    csv_data = generate_csv()
    if csv_data:
        trigger_download(csv_data)
        show_status(f"Exported {len(RECORDS)} records", "success")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main initialization function"""
    load_records()
    
    # Set current timestamp
    js.document.getElementById("timestamp").value = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    # Set up event handlers
    js.document.getElementById("save-btn").addEventListener("click", save_entry)
    js.document.getElementById("clear-btn").addEventListener("click", clear_form)
    js.document.getElementById("export-btn").addEventListener("click", export_csv)
    
    def confirm_clear(event):
        result = js.confirm("Are you sure you want to clear ALL records? This cannot be undone.")
        if result:
            clear_all_records()
    
    js.document.getElementById("clear-all-btn").addEventListener("click", confirm_clear)
    
    update_record_count()
    show_status("Feed Form ready", "success")


def save_entry(event=None):
    """Save the current form entry"""
    if not validate_form():
        return
    
    record = get_form_data()
    add_record(record)
    clear_form()
    show_status("Entry saved", "success")


# Run main when DOM is loaded
js.document.addEventListener("DOMContentLoaded", main)
