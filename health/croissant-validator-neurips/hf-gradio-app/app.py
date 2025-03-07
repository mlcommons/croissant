import gradio as gr
import json
import time
import traceback
from validation import validate_json, validate_croissant, validate_records
import requests

def process_file(file):
    results = []
    
    # Check 1: JSON validation
    json_valid, json_message, json_data = validate_json(file.name)
    results.append(("JSON Format Validation", json_valid, json_message))
    
    if not json_valid:
        return results
    
    # Check 2: Croissant validation
    croissant_valid, croissant_message = validate_croissant(json_data)
    results.append(("Croissant Schema Validation", croissant_valid, croissant_message))
    
    if not croissant_valid:
        return results
    
    # Check 3: Records validation
    records_valid, records_message = validate_records(json_data)
    results.append(("Records Generation Test", records_valid, records_message))
    
    return results

def create_ui():
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🔎🥐 Croissant JSON-LD Validator for NeurIPS")
        gr.Markdown("""
        Upload your Croissant JSON-LD file or enter a URL to validate if it meets the requirements for NeurIPS submission.
        The validator will check:
        1. If the file is valid JSON
        2. If it passes Croissant schema validation
        3. If records can be generated within a reasonable time
        """)
        
        # Track the active tab for conditional UI updates
        active_tab = gr.State("upload")  # Default to upload tab
        
        # Create a container for the entire input section
        with gr.Group():
            # Input tabs
            with gr.Tabs() as tabs:
                with gr.TabItem("Upload File", id="upload_tab"):
                    file_input = gr.File(label="Upload Croissant JSON-LD File", file_types=[".json", ".jsonld"])
                    validate_btn = gr.Button("Validate Uploaded File", variant="primary")
                
                with gr.TabItem("URL Input", id="url_tab"):
                    url_input = gr.Textbox(
                        label="Enter Croissant JSON-LD URL",
                        placeholder="e.g. https://huggingface.co/api/datasets/facebook/natural_reasoning/croissant"
                    )
                    fetch_btn = gr.Button("Fetch and Validate", variant="primary")
            
            # Change initial message to match upload tab
            upload_progress = gr.HTML(
                """<div class="progress-status">Ready for upload</div>""", 
                visible=True)
        
        # Now create the validation results section in a separate group
        with gr.Group():
            # Validation results
            validation_results = gr.HTML(visible=False)
        
        # Define CSS for the validation UI
        gr.HTML("""
        <style>
        /* Set max width and center the app */
        .gradio-container {
            max-width: 750px !important;
            margin: 0 auto !important;
        }

        /* Make basic containers transparent */
        .gr-group, .gr-box, .gr-panel, .gradio-box, .gradio-group {
            background-color: var(--body-background-fill) !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Style for expandable validation steps */
        .validation-step {
            margin-bottom: 12px;
            border: 1px solid var(--border-color-primary, rgba(128, 128, 128, 0.2));
            border-radius: 8px;
            overflow: hidden;
        }

        .step-header {
            padding: 10px 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            background-color: rgba(0, 0, 0, 0.03) !important;
        }

        .step-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Force text color to white in status indicators */
        .step-status {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white !important;
        }

        .status-success {
            background-color: #4caf50 !important;
        }

        .status-error {
            background-color: #f44336 !important;
        }

        .step-details {
            padding: 12px 15px;
            background-color: var(--body-background-fill) !important;
        }

        /* User hints styling - italic, smaller, better positioned */
        .progress-status {
            font-style: italic;
            font-size: 0.9em;
            color: var(--body-text-color-subdued);
            padding: 8px 0;
            margin-top: 5px;
            width: 100%;
            background: none !important;
            border: none !important;
            text-align: center;
        }

        /* Override input containers to match page background */
        .gr-input-container, .gr-form, .gr-input, .gr-box, .gr-panel,
        .file-preview, .file-preview > div {
            background-color: var(--body-background-fill) !important;
        }

        /* Ensure buttons have proper styling */
        button.primary, button[data-testid="primary-button"] {
            background-color: var(--primary-500) !important;
            color: white !important;
        }

        /* Arrow indicator for expandable sections */
        .arrow-indicator {
            font-size: 14px;
            transition: transform 0.3s ease;
        }
        .arrow-down {
            transform: rotate(90deg);
        }
        </style>
        """)
        
        # Update helper messages based on tab changes
        def on_tab_change(evt: gr.SelectData):
            tab_id = evt.value
            if tab_id == "Upload File":
                return "upload", """<div class="progress-status">Ready for upload</div>""", gr.update(visible=False)
            else:
                return "url", """<div class="progress-status">Enter a URL to fetch</div>""", gr.update(visible=False)
        
        def on_file_upload(file):
            if file is None:
                return """<div class="progress-status">Ready for upload</div>""", gr.update(visible=False)
            
            return """<div class="progress-status">✅ File uploaded successfully</div>""", gr.update(visible=False)
        
        def fetch_from_url(url):
            if not url:
                return """<div class="progress-status">Please enter a URL</div>""", gr.update(visible=False)
            
            try:
                # Fetch JSON from URL
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                json_data = response.json()
                
                # Show success message
                progress_html = """<div class="progress-status">✅ JSON fetched successfully from URL</div>"""
                
                # Validate the fetched JSON
                results = []
                results.append(("JSON Format Validation", True, "✅ The URL returned valid JSON."))
                
                croissant_valid, croissant_message = validate_croissant(json_data)
                results.append(("Croissant Schema Validation", croissant_valid, croissant_message))
                
                if not croissant_valid:
                    return progress_html, build_results_html(results)
                
                records_valid, records_message = validate_records(json_data)
                results.append(("Records Generation Test", records_valid, records_message))
                
                return progress_html, build_results_html(results)
                
            except requests.exceptions.RequestException as e:
                error_message = f"❌ Error fetching URL: {str(e)}"
                return f"""<div class="progress-status">{error_message}</div>""", gr.update(visible=False)
            except json.JSONDecodeError as e:
                error_message = f"❌ URL did not return valid JSON: {str(e)}"
                return f"""<div class="progress-status">{error_message}</div>""", gr.update(visible=False)
            except Exception as e:
                error_message = f"❌ Unexpected error: {str(e)}"
                return f"""<div class="progress-status">{error_message}</div>""", gr.update(visible=False)
        
        def build_results_html(results):
            # Build validation results HTML
            html = '<div class="validation-results">'
            
            for i, (test_name, passed, message) in enumerate(results):
                status_class = "status-success" if passed else "status-error"
                status_icon = "✓" if passed else "✗"
                
                html += f'''
                <div class="validation-step" id="step-{i}">
                    <div class="step-header" onclick="
                        var details = document.getElementById('details-{i}');
                        var arrow = document.getElementById('arrow-{i}');
                        if(details.style.display === 'none') {{
                            details.style.display = 'block';
                            arrow.classList.add('arrow-down');
                        }} else {{
                            details.style.display = 'none';
                            arrow.classList.remove('arrow-down');
                        }}">
                        <div class="step-left">
                            <div class="step-status {status_class}">{status_icon}</div>
                            <div class="step-title">{test_name}</div>
                            <div class="arrow-indicator" id="arrow-{i}">▶</div>
                        </div>
                    </div>
                    <div class="step-details" id="details-{i}" style="display: none;">
                        {message}
                    </div>
                </div>
                '''
            
            html += '</div>'
            return gr.update(value=html, visible=True)
        
        def on_validate(file):
            if file is None:
                return gr.update(visible=False)
            
            # Process the file and get results
            results = process_file(file)
            return build_results_html(results)
        
        # Connect UI events to functions
        tabs.select(on_tab_change, None, [active_tab, upload_progress, validation_results])
        file_input.change(on_file_upload, inputs=file_input, outputs=[upload_progress, validation_results])
        validate_btn.click(on_validate, inputs=file_input, outputs=validation_results)
        fetch_btn.click(fetch_from_url, inputs=url_input, outputs=[upload_progress, validation_results])
        
        # Footer
        gr.HTML("""
        <div style="text-align: center; margin-top: 20px;">
            <p>Learn more about <a href="https://github.com/mlcommons/croissant" target="_blank">Croissant format</a>.</p>
        </div>
        """)
    
    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch() 