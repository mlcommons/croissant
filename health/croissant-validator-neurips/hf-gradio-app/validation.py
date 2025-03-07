import json
import traceback
import mlcroissant as mlc
import func_timeout

ONE_MINUTE = 60  # seconds

def validate_json(file_path):
    """Validate that the file is proper JSON."""
    try:
        with open(file_path, 'r') as f:
            json_data = json.load(f)
        return True, "✅ The file is valid JSON.", json_data
    except json.JSONDecodeError as e:
        error_message = f"❌ Invalid JSON format: {str(e)}"
        return False, error_message, None
    except Exception as e:
        error_message = f"❌ Error reading file: {str(e)}"
        return False, error_message, None

def validate_croissant(json_data):
    """Validate that the JSON follows Croissant schema."""
    try:
        dataset = mlc.Dataset(jsonld=json_data)
        return True, "✅ The dataset passes Croissant validation."
    except mlc.ValidationError as e:
        error_details = traceback.format_exc()
        error_message = f"❌ Validation failed: {str(e)}\n\n{error_details}"
        return False, error_message
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"❌ Unexpected error during validation: {str(e)}\n\n{error_details}"
        return False, error_message

def validate_records(json_data):
    """Validate that records can be generated within the time limit."""
    try:
        dataset = mlc.Dataset(jsonld=json_data)
        record_sets = dataset.metadata.record_sets
        
        if not record_sets:
            return True, "✅ No record sets found to validate."
        
        results = []
        
        for record_set in record_sets:
            try:
                records = dataset.records(record_set=record_set.name)
                _ = func_timeout.func_timeout(ONE_MINUTE, lambda: next(iter(records)))
                results.append(f"✅ Record set '{record_set.name}' passed validation.")
            except func_timeout.exceptions.FunctionTimedOut:
                error_message = f"❌ Record set '{record_set.name}' generation took too long (>60s)"
                return False, error_message
            except Exception as e:
                error_details = traceback.format_exc()
                error_message = f"❌ Record set '{record_set.name}' failed: {str(e)}\n\n{error_details}"
                return False, error_message
        
        return True, "\n".join(results)
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"❌ Unexpected error during records validation: {str(e)}\n\n{error_details}"
        return False, error_message 