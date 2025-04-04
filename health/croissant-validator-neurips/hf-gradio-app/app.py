import gradio as gr
import json
import time
import traceback
from validation import validate_json, validate_croissant, validate_records, generate_validation_report
import requests

def process_file(file):
    results = []
    json_data = None
    
    # Use just the filename instead of full path
    filename = file.name.split("/")[-1]
    
    # Check 1: JSON validation
    json_valid, json_message, json_data = validate_json(file.name)
    # Remove empty checkmarks from messages
    json_message = json_message.replace("\n✓\n", "\n")
    results.append(("JSON Format Validation", json_valid, json_message))
    
    if not json_valid:
        return results, None
    
    # Check 2: Croissant validation
    croissant_valid, croissant_message = validate_croissant(json_data)
    # Remove empty checkmarks from messages
    croissant_message = croissant_message.replace("\n✓\n", "\n")
    results.append(("Croissant Schema Validation", croissant_valid, croissant_message))
    
    if not croissant_valid:
        return results, None
    
    # Check 3: Records validation
    records_valid, records_message = validate_records(json_data)
    # Remove empty checkmarks from messages
    records_message = records_message.replace("\n✓\n", "\n")
    results.append(("Records Generation Test", records_valid, records_message))
    
    # Generate detailed report with just filename
    report = generate_validation_report(filename, json_data, results)
    
    return results, report

def create_ui():
    with gr.Blocks(theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🔎🥐 Croissant Validator for NeurIPS D&B")
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
            validation_progress = gr.HTML(visible=False)
            
            # Collapsible report section
            with gr.Accordion("Download full validation report", visible=False, open=False) as report_group:
                with gr.Column():
                    report_md = gr.File(
                        label="Download Report",
                        visible=True,
                        file_types=[".md"]
                    )
                    report_text = gr.Textbox(
                        label="Report Content", 
                        visible=True,
                        show_copy_button=True,
                        lines=10
                    )

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
            transform: rotate(0deg);  /* Point right by default */
        }
        .arrow-down {
            transform: rotate(90deg);  /* Point down when expanded */
        }

        /* Loading animation */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top-color: var(--primary-500);
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .validation-progress {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            margin: 10px 0;
            background-color: var(--background-fill-secondary);
            border-radius: 8px;
        }

        /* Override Gradio's default accordion arrow */
        .gr-accordion {
            position: relative;
        }
        .gr-accordion > .label-wrap {
            display: flex;
            align-items: center;
            gap: 8px;
            padding-right: 32px;  /* Make room for the arrow */
        }
        .gr-accordion > .label-wrap::after {
            content: "▶";
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            transition: transform 0.3s ease;
            font-size: 0.8em;
        }
        .gr-accordion[data-open=true] > .label-wrap::after {
            transform: translateY(-50%) rotate(90deg);
        }

        /* Consistent arrow styling for both validation steps and accordion */
        .validation-step .step-header,
        .gr-accordion > .label-wrap {
            position: relative;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .validation-step .arrow-indicator,
        .gr-accordion > .label-wrap::after {
            content: "▶";
            font-size: 0.8em;
            margin-left: 8px;
            transition: transform 0.3s ease;
        }

        /* Remove absolute positioning and right alignment for accordion arrow */
        .gr-accordion > .label-wrap {
            padding-right: 0;  /* Remove extra padding */
        }
        .gr-accordion > .label-wrap::after {
            position: static;  /* Remove absolute positioning */
            right: auto;
            transform: none;
        }

        /* Consistent rotation for expanded state */
        .validation-step .arrow-down,
        .gr-accordion[data-open=true] > .label-wrap::after {
            transform: rotate(90deg);
        }
        </style>
        """)
        
        # Update helper messages based on tab changes
        def on_tab_change(evt: gr.SelectData):
            tab_id = evt.value
            if tab_id == "Upload File":
                return [
                    "upload",
                    """<div class="progress-status">Ready for upload</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),  # Hide report group
                    None,  # Clear report text
                    None,  # Clear report file
                    None,  # Clear file input
                    gr.update(value="")  # Clear URL input
                ]
            else:
                return [
                    "url",
                    """<div class="progress-status">Enter a URL to fetch</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),  # Hide report group
                    None,  # Clear report text
                    None,  # Clear report file
                    None,  # Clear file input
                    gr.update(value="")  # Clear URL input
                ]
        
        def on_copy_click(report):
            return report
            
        def on_download_click(report, file_name):
            report_file = f"report_{file_name}.md"
            with open(report_file, "w") as f:
                f.write(report)
            return report_file
        
        def on_file_upload(file):
            if file is None:
                return [
                    """<div class="progress-status">Ready for upload</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),  # Hide report group
                    None,  # Clear report text
                    None   # Clear report file
                ]
            
            return [
                """<div class="progress-status">✅ File uploaded successfully</div>""",
                gr.update(visible=False),
                gr.update(visible=False),  # Hide report group
                None,  # Clear report text
                None   # Clear report file
            ]
        
        def fetch_from_url(url):
            if not url:
                return [
                    """<div class="progress-status">Please enter a URL</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    None,
                    None
                ]
            
            try:
                # Fetch JSON from URL
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                json_data = response.json()
                
                # Process validation
                results = []
                results.append(("JSON Format Validation", True, "The URL returned valid JSON."))
                
                croissant_valid, croissant_message = validate_croissant(json_data)
                results.append(("Croissant Schema Validation", croissant_valid, croissant_message))
                
                if not croissant_valid:
                    return [
                        """<div class="progress-status">✅ JSON fetched successfully from URL</div>""",
                        build_results_html(results),
                        gr.update(visible=False),
                        None,
                        None
                    ]
                
                records_valid, records_message = validate_records(json_data)
                results.append(("Records Generation Test", records_valid, records_message))
                
                # Generate report
                report = generate_validation_report(url.split("/")[-1], json_data, results)
                report_filename = f"report_croissant-validation_{json_data.get('name', 'unnamed')}.md"
                
                if report:
                    with open(report_filename, "w") as f:
                        f.write(report)
                
                return [
                    """<div class="progress-status">✅ JSON fetched successfully from URL</div>""",
                    build_results_html(results),
                    gr.update(visible=True),
                    report,
                    report_filename
                ]
                
            except requests.exceptions.RequestException as e:
                error_message = f"Error fetching URL: {str(e)}"
                return [
                    f"""<div class="progress-status">{error_message}</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    None,
                    None
                ]
            except json.JSONDecodeError as e:
                error_message = f"URL did not return valid JSON: {str(e)}"
                return [
                    f"""<div class="progress-status">{error_message}</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    None,
                    None
                ]
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                return [
                    f"""<div class="progress-status">{error_message}</div>""",
                    gr.update(visible=False),
                    gr.update(visible=False),
                    None,
                    None
                ]
        
        def build_results_html(results):
            # Build validation results HTML
            html = '<div class="validation-results">'
            
            for i, (test_name, passed, message) in enumerate(results):
                status_class = "status-success" if passed else "status-error"
                status_icon = "✓" if passed else "✗"
                # Add emoji to message
                message_with_emoji = ("✅ " if passed else "❌ ") + message
                
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
                            <span class="step-title">{test_name}</span>
                            <span class="arrow-indicator" id="arrow-{i}">▶</span>
                        </div>
                    </div>
                    <div class="step-details" id="details-{i}" style="display: none;">
                        {message_with_emoji}
                    </div>
                </div>
                '''
            
            html += '</div>'
            return gr.update(value=html, visible=True)
        
        def on_validate(file):
            if file is None:
                return [
                    gr.update(visible=False),  # validation_results
                    gr.update(visible=False),  # validation_progress
                    gr.update(visible=False),  # report_group
                    None,  # report_text
                    None   # report_md
                ]
            
            # Process the file and get results
            results, report = process_file(file)
            
            # Extract dataset name from the JSON for the report filename
            try:
                with open(file.name, 'r') as f:
                    json_data = json.load(f)
                dataset_name = json_data.get('name', 'unnamed')
            except:
                dataset_name = 'unnamed'
            
            # Save report to file with new naming convention
            report_filename = f"report_croissant-validation_{dataset_name}.md"
            if report:
                with open(report_filename, "w") as f:
                    f.write(report)
            
            # Return final state
            return [
                build_results_html(results),  # validation_results
                gr.update(visible=False),  # validation_progress
                gr.update(visible=True) if report else gr.update(visible=False),  # report_group
                report if report else None,  # report_text
                report_filename if report else None  # report_md
            ]
        
        # Connect UI events to functions with updated outputs
        tabs.select(
            on_tab_change,
            None,
            [active_tab, upload_progress, validation_results, report_group, report_text, report_md, file_input, url_input]
        )
        file_input.change(
            on_file_upload,
            inputs=file_input,
            outputs=[upload_progress, validation_results, report_group, report_text, report_md]
        )
        
        # Add progress state handling
        def show_progress():
            progress_html = """
            <div class="validation-progress">
                <div class="loading-spinner"></div>
                <span>Validating file...</span>
            </div>
            """
            return [
                gr.update(visible=False),  # validation_results
                gr.update(visible=True, value=progress_html),  # validation_progress
                gr.update(visible=False),  # report_group
                None,  # report_text
                None   # report_md
            ]
        
        validate_btn.click(
            fn=show_progress,
            inputs=None,
            outputs=[validation_results, validation_progress, report_group, report_text, report_md],
            queue=False
        ).then(
            fn=on_validate,
            inputs=file_input,
            outputs=[validation_results, validation_progress, report_group, report_text, report_md]
        )
        
        fetch_btn.click(
            fetch_from_url,
            inputs=url_input,
            outputs=[upload_progress, validation_results, report_group, report_text, report_md]
        )
        
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
