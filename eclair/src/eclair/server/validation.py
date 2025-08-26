import mlcroissant as mlc
import func_timeout
import json
import traceback

WAIT_TIME = 10 * 60  # seconds

def validate_json(json_string):
    """Validate that the string is proper JSON."""
    try:
        json_data = json.loads(json_string)
        return True, "The string is valid JSON.", json_data
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON format: {str(e)}"
        return False, error_message, None
    except Exception as e:
        error_message = f"Error parsing JSON string: {str(e)}"
        return False, error_message, None

def validate_croissant(json_data):
    """Validate that the JSON follows Croissant schema."""
    try:
        dataset = mlc.Dataset(jsonld=json_data)
        return True, "The dataset passes Croissant validation."
    except mlc.ValidationError as e:
        error_details = traceback.format_exc()
        error_message = f"Validation failed: {str(e)}\n\n{error_details}"
        return False, error_message
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"Unexpected error during validation: {str(e)}\n\n{error_details}"
        return False, error_message
    
def try_generate_record(record_collection):
    try:
        for i, record in enumerate(record_collection):
            if i == 0:
                break
        return "success"
    except Exception as e:
        return e

def validate_records(json_data):
    """Validate that records can be generated within the time limit."""
    try:
        dataset = mlc.Dataset(jsonld=json_data)
        record_sets = dataset.metadata.record_sets
        
        if not record_sets:
            return True, "No record sets found to validate.", "pass"
        
        results = []
        
        for record_set in record_sets:
            try:
                result = func_timeout.func_timeout(
                    WAIT_TIME,
                    lambda: try_generate_record(dataset.records(record_set=record_set.uuid))
                )

                if isinstance(result, Exception):
                    raise result  # re-raise actual error outside timeout

                results.append(f"Record set '{record_set.uuid}' passed validation.")

            except func_timeout.exceptions.FunctionTimedOut:
                error_message = f"Record set '{record_set.uuid}' generation took too long (>10 minutes)."
                return False, error_message, "warning"

            except Exception as e:
                error_details = traceback.format_exc()
                error_message = (
                    f"Record set '{record_set.uuid}' failed due to generation error:\n\n"
                    f"```text\n{str(e)}\n\n{error_details}```"
                )
                return False, error_message, "warning"
        
        return True, "\n".join(results), "pass"
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"Unexpected error during records validation: {str(e)}\n\n{error_details}"
        return False, error_message, "error"

def validate(json_string):
    """Validate a JSON string containing Croissant metadata."""
    results = []
    json_data = None

    # Check 1: JSON validation
    json_valid, json_message, json_data = validate_json(json_string)
    json_message = json_message.replace("\n✓\n", "\n")
    results.append(("JSON Format Validation", json_valid, json_message, "pass" if json_valid else "error"))

    if not json_valid:
        return results, None

    # Check 2: Croissant validation
    croissant_valid, croissant_message = validate_croissant(json_data)
    croissant_message = croissant_message.replace("\n✓\n", "\n")
    results.append(("Croissant Schema Validation", croissant_valid, croissant_message, "pass" if croissant_valid else "error"))

    if not croissant_valid:
        return results, None

    # Check 3: Records validation (with timeout-safe and error-specific logic)
    records_valid, records_message, records_status = validate_records(json_data)
    records_message = records_message.replace("\n✓\n", "\n")
    results.append(("Records Generation Test", records_valid, records_message, records_status))

    return results