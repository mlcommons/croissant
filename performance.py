import time

import mlcroissant as mlc

start_time = time.time()

dataset = mlc.Dataset(
    # jsonld="https://huggingface.co/api/datasets/BleachNick/UltraEdit_500k/croissant",
    jsonld="https://huggingface.co/api/datasets/ylecun/mnist/croissant",
)

very_start = time.time()
for idx, record in enumerate(dataset.records("mnist")):
    if idx == 0:
        print(f"Time to first element: {(time.time() - start_time):.2f} seconds.")
        start_time = time.time()
    elif idx % 1000 == 0:
        print(f"Processed {idx} in {(time.time() - start_time):.2f} seconds.")
        start_time = time.time()
    continue

print(f"Total in {(time.time() - very_start):.2f} seconds.")
