import pytdml.io
from pytdml.ml.tdml_torch_data_pipe import TorchSemanticSegmentationDataPipe
from torchvision import transforms

# Load the TDML dataset
training_dataset = pytdml.io.read_from_json("hls_burn_scars_tdml.json")

# Define your class list (order matters: background, burn_scar)
class_list = ["background", "burn_scar"]

# Set up a cache path for downloaded files
cache_path = "./tdml_cache_segmentation.pkl"

# Create the DataPipe
data_pipe = TorchSemanticSegmentationDataPipe(
    training_dataset.data,
    root=".",  # Local directory to cache files
    cache_path=cache_path,
    class_list=class_list,
    crop=None,
    transform=transforms.ToTensor()
)

# Get the first sample (downloads and caches if needed)
img, mask = next(iter(data_pipe))
print("Image shape:", img.shape)
print("Mask shape:", mask.shape) 
