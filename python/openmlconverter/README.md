# OpenML to MLCommons converter 

This repository contains the code to convert from the OpenML dataset schema to the new DCF (aka 
"Croissant") format.


# Install
Using python 3.11:
```
python -m pip install "."
``` 
Or, if you want to do development:
```
python -m pip install ".[dev]"
```

# Usage
```
python3 src/main.py --id [openml-id] --output [your-output-dir]
```
Example:
```
python3 src/main.py --id 2 --output output
```


