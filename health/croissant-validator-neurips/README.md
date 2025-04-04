In order to validate whether a croissant file is JSON-LD, conforms to the Croissant schema and is able to yield records we have currently two tools:

### Option 1: Colab

Access the notebook at https://colab.research.google.com/drive/1W9tSMv7OMv2nPLrbTpbCypEjv6Z3ZcxF and validate your Croissant file.

### Option 2: Public gradio app hosted on HF Spaces

We have a reference implementation that you are free to adapt in `/hf-gradio-app`.

To host your own validator app you can commit the contents of that folder to a HF Gradio Space, run it locally `python app.py` or otherwise on a VM of your choice. 

Some examples of live spaces can be found at

* https://huggingface.co/spaces/JoaquinVanschoren/croissant-checker
* https://huggingface.co/spaces/luisoala/croissant-checker
