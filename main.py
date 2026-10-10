"""
Feed Form - Main application logic
Offline-first data entry for scale readings and material selection
"""

import json
import js
from datetime import datetime

# Global configuration
CONFIG = None
RECORDS = []
STORAGE_KEY = "feed_form_records"


def load_config():
    """Load configuration from conf.json"""
    global CONFIG
    config_element = js.document.getElementById("py-script-1")
    if config_element and hasattr(config_element, 'innerText'):
        CONFIG = json.loads(config_element.innerText)
    else:
        # Fallback: try to fetch from file
        try:
            with open("conf.json", "r") as f:
                CONFIG = json.loads(f.read())
        except:
            CONFIG = {
                "fields": {
                    "scale_readings": [
                        {"id": "weight_1", "label": "Weight 1", "type": "number", "unit": "kg"},
                        {"id": "weight_2", "label": "Weight 2", "type": "number", "unit": "kg"}
                    ],
                    "material": {
                        "id": "material",
                        "label": "Material",
                        "type": "select",
                        "options": ["Material A", "Material B"]
                    },
                    "notes": {"id": "notes", "label": "Notes", "type": "text", "required": False}
                },
                "storage_key": "feed_form_records",
                "csv_filename": "feed_form_export.csv"
            }
    return CONFIG


def load_records():
    """Load records from browser localStorage"""
    global RECORDS
    config = load_config()
    storage_key = config.get("storage_key", STORAGE_KEY)
    
    try:
        stored = js.localStorage.getItem(storage_key)
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
    config = load_config()
    storage_key = config.get("storage_key", STORAGE_KEY)
    
    try:
        js.localStorage.setItem(storage_key, json.dumps(RECORDS))
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
    config = load_config()
    storage_key = config.get("storage_key", STORAGE_KEY)
    
    try:
        js.localStorage.removeItem(storage_key)
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


def get_form_data():
    """Extract form data from the HTML form"""
    config = load_config()
    fields = config.get("fields", {})
    
    record = {
        "timestamp": js.document.getElementById("timestamp").value
    }
    
    # Get material selection
    material_field = fields.get("material", {})
    material_id = material_field.get("id", "material")
    material_element = js.document.getElementById(material_id)
    if material_element:
        record[material_id] = material_element.value
    
    # Get scale readings
    scale_readings = fields.get("scale_readings", [])
    for reading in scale_readings:
        field_id = reading.get("id", "")
        element = js.document.getElementById(field_id)
        if element:
            value = element.value
            if value:
                try:
                    record[field_id] = float(value)
                except:
                    record[field_id] = value
            else:
                record[field_id] = None
    
    # Get notes
    notes_field = fields.get("notes", {})
    notes_id = notes_field.get("id", "notes")
    notes_element = js.document.getElementById(notes_id)
    if notes_element:
        record[notes_id] = notes_element.value
    
    return record


def validate_form():
    """Validate form inputs"""
    config = load_config()
    fields = config.get("fields", {})
    
    # Check required material
    material_field = fields.get("material", {})
    material_id = material_field.get("id", "material")
    material_element = js.document.getElementById(material_id)
    
    if not material_element or not material_element.value:
        show_status("Please select a material", "error")
        return False
    
    # Check at least one scale reading
    scale_readings = fields.get("scale_readings", [])
    has_reading = False
    for reading in scale_readings:
        field_id = reading.get("id", "")
        element = js.document.getElementById(field_id)
        if element and element.value:
            has_reading = True
            break
    
    if not has_reading:
        show_status("Please enter at least one scale reading", "error")
        return False
    
    # Check timestamp
    timestamp_element = js.document.getElementById("timestamp")
    if not timestamp_element or not timestamp_element.value:
        show_status("Please enter a timestamp", "error")
        return False
    
    return True


def clear_form():
    """Clear the form fields"""
    config = load_config()
    fields = config.get("fields", {})
    
    # Clear timestamp
    timestamp_element = js.document.getElementById("timestamp")
    if timestamp_element:
        timestamp_element.value = ""
    
    # Clear material
    material_field = fields.get("material", {})
    material_id = material_field.get("id", "material")
    material_element = js.document.getElementById(material_id)
    if material_element:
        material_element.value = ""
    
    # Clear scale readings
    scale_readings = fields.get("scale_readings", [])
    for reading in scale_readings:
        field_id = reading.get("id", "")
        element = js.document.getElementById(field_id)
        if element:
            element.value = ""
    
    # Clear notes
    notes_field = fields.get("notes", {})
    notes_id = notes_field.get("id", "notes")
    notes_element = js.document.getElementById(notes_id)
    if notes_element:
        notes_element.value = ""
    
    show_status("Form cleared", "success")


def generate_csv():
    """Generate CSV data from stored records"""
    load_records()
    config = load_config()
    
    if not RECORDS:
        show_status("No records to export", "error")
        return None
    
    # Build header row
    fields = config.get("fields", {})
    header = ["timestamp"]
    
    # Add material column
    material_field = fields.get("material", {})
    material_id = material_field.get("id", "material")
    header.append(material_id)
    
    # Add scale reading columns
    scale_readings = fields.get("scale_readings", [])
    for reading in scale_readings:
        header.append(reading.get("id", ""))
    
    # Add notes column
    notes_field = fields.get("notes", {})
    notes_id = notes_field.get("id", "notes")
    header.append(notes_id)
    
    # Build data rows
    rows = []
    for record in RECORDS:
        row = []
        
        # Timestamp
        ts = record.get("timestamp", "")
        row.append(ts)
        
        # Material
        row.append(record.get(material_id, ""))
        
        # Scale readings
        for reading in scale_readings:
            field_id = reading.get("id", "")
            value = record.get(field_id, "")
            if isinstance(value, (int, float)):
                row.append(str(value))
            else:
                row.append(str(value) if value else "")
        
        # Notes
        row.append(record.get(notes_id, ""))
        
        rows.append(row)
    
    # Build CSV content
    csv_lines = [",".join(header)]
    for row in rows:
        # Escape commas and quotes
        escaped_row = []
        for cell in row:
            cell_str = str(cell) if cell else ""
            if "," in cell_str or '"' in cell_str or "\n" in cell_str:
                cell_str = f'"{cell_str.replace("\"", "\\\"")}"'
            escaped_row.append(cell_str)
        csv_lines.append(",".join(escaped_row))
    
    return "\n".join(csv_lines)


def trigger_download(csv_data, filename):
    """Trigger a file download in the browser"""
    config = load_config()
    csv_filename = config.get("csv_filename", filename)
    
    blob = js.Blob.new([csv_data], {"type": "text/csv"})
    url = js.URL.createObjectURL(blob)
    
    a = js.document.createElement("a")
    a.href = url
    a.download = csv_filename
    js.document.body.appendChild(a)
    a.click()
    js.document.body.removeChild(a)
    js.URL.revokeObjectURL(url)


def export_csv(event=None):
    """Export records as CSV file"""
    csv_data = generate_csv()
    if csv_data:
        config = load_config()
        filename = config.get("csv_filename", "feed_form_export.csv")
        trigger_download(csv_data, filename)
        show_status(f"Exported {len(RECORDS)} records", "success")


def save_entry(event=None):
    """Save the current form entry"""
    if not validate_form():
        return
    
    record = get_form_data()
    
    # Ensure timestamp is set
    if not record.get("timestamp"):
        record["timestamp"] = datetime.now().isoformat()
    
    add_record(record)
    clear_form()
    show_status("Entry saved", "success")


def init_form():
    """Initialize the form with field definitions from config"""
    config = load_config()
    fields = config.get("fields", {})
    
    # Set up timestamp with current time
    timestamp_element = js.document.getElementById("timestamp")
    if timestamp_element:
        timestamp_element.value = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    # Populate material dropdown
    material_field = fields.get("material", {})
    material_id = material_field.get("id", "material")
    material_element = js.document.getElementById(material_id)
    if material_element:
        options = material_field.get("options", [])
        material_element.innerHTML = ""
        
        # Add default empty option
        option = js.document.createElement("option")
        option.value = ""
        option.text = "-- Select Material --"
        material_element.appendChild(option)
        
        for opt in options:
            option = js.document.createElement("option")
            option.value = opt
            option.text = opt
            material_element.appendChild(option)
    
    # Create scale reading fields
    scale_readings = fields.get("scale_readings", [])
    scale_fields_container = js.document.getElementById("scale-fields")
    if scale_fields_container and scale_readings:
        scale_fields_container.innerHTML = ""
        
        for reading in scale_readings:
            field_id = reading.get("id", "")
            label = reading.get("label", field_id)
            unit = reading.get("unit", "")
            
            # Create field container
            field_div = js.document.createElement("div")
            field_div.className = "scale-field"
            
            # Create label
            label_element = js.document.createElement("label")
            label_element.htmlFor = field_id
            label_element.textContent = f"{label} ({unit})"
            field_div.appendChild(label_element)
            
            # Create input
            input_element = js.document.createElement("input")
            input_element.type = "number"
            input_element.id = field_id
            input_element.className = "form-control"
            input_element.step = "0.01"
            input_element.placeholder = "0.00"
            field_div.appendChild(input_element)
            
            scale_fields_container.appendChild(field_div)
    
    # Update record count
    update_record_count()


def setup_event_handlers():
    """Set up event handlers for form buttons"""
    # Save button
    save_btn = js.document.getElementById("save-btn")
    if save_btn:
        save_btn.addEventListener("click", save_entry)
    
    # Clear form button
    clear_btn = js.document.getElementById("clear-btn")
    if clear_btn:
        clear_btn.addEventListener("click", clear_form)
    
    # Export button
    export_btn = js.document.getElementById("export-btn")
    if export_btn:
        export_btn.addEventListener("click", export_csv)
    
    # Clear all button
    clear_all_btn = js.document.getElementById("clear-all-btn")
    if clear_all_btn:
        def confirm_clear(event):
            result = js.confirm("Are you sure you want to clear ALL records? This cannot be undone.")
            if result:
                clear_all_records()
        
        clear_all_btn.addEventListener("click", confirm_clear)


def main():
    """Main initialization function"""
    load_config()
    load_records()
    init_form()
    setup_event_handlers()
    show_status("Feed Form ready", "success")


# Run main when DOM is loaded
js.document.addEventListener("DOMContentLoaded", main)
