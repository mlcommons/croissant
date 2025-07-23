#!/usr/bin/env python3
#python hls_burn_scars_tdml.py
"""
Complete TDML Generator for HLS Burn Scars Dataset
Reads .gitattributes file to discover all actual files and generates comprehensive TDML Metadata
"""

import os
import json
import re
from typing import List, Dict, Any, Set
from pytdml.io import write_to_json
from pytdml.type import EOTrainingDataset, AI_EOTrainingData, AI_EOTask, AI_PixelLabel, MD_Band
from pytdml.type.basic_types import NamedValue

class HLSBurnScarsCompleteTDMLGenerator:
    def __init__(self, base_url: str = "https://huggingface.co/datasets/harshinde/hls_burn_scars/resolve/main"):
        self.base_url = base_url
        self.splits = ["training", "validation"]  # Based on .gitattributes structure
        self.classes = ["background", "burn_scar"]
        
        # Metadata from your gdalinfo output
        self.crs = "EPSG:32610"  # UTM Zone 10N
        self.resolution = [30, 30]  # meters
        self.image_size = [512, 512]  # pixels
        self.extent = [491220.0, 4266540.0, 506580.0, 4281900.0]  # [xmin, ymin, xmax, ymax]
        
    def parse_gitattributes(self, gitattributes_path: str = ".gitattributes") -> Dict[str, List[str]]:
        """
        Parse .gitattributes file to discover all tile IDs in the dataset
        Returns: Dict with split -> set of tile IDs
        """
        tile_ids = {"training": set(), "validation": set()}
        
        if not os.path.exists(gitattributes_path):
            print(f"Warning: {gitattributes_path} not found. Using sample data.")
            return self.get_sample_tile_ids()
        
        print(f"Reading {gitattributes_path}...")
        
        with open(gitattributes_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse file path: training/subsetted_512x512_HLS.S30.{TILE_ID}_merged.tif
                # or: training/subsetted_512x512_HLS.S30.{TILE_ID}.mask.tif
                match = re.match(r'(training|validation)/subsetted_512x512_HLS\.S30\.(.+?)(_merged|\.mask)\.tif', line)
                if match:
                    split = match.group(1)
                    tile_id = match.group(2)
                    tile_ids[split].add(tile_id)
        
        # Convert sets to sorted lists for consistent output
        return {split: sorted(list(tile_set)) for split, tile_set in tile_ids.items()}
    
    def get_sample_tile_ids(self) -> Dict[str, List[str]]:
        """Fallback sample tile IDs if .gitattributes is not available"""
        return {
            "training": [
                "T10SDH.2020248.v1.4",
                "T10SEH.2018245.v1.4", 
                "T10SEH.2018280.v1.4"
            ],
            "validation": [
                "T10SDH.2020248.v1.4",
                "T10SEH.2018245.v1.4"
            ]
        }
    
    def create_bands(self) -> List[MD_Band]:
        """Create band definitions based on HLS S30 data"""
        bands = []
        band_names = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]
        
        for i, name in enumerate(band_names, 1):
            band = MD_Band(
                sequence_identifier=None,
                description=f"Band {i} ({name})",
                name=None,
                max_value=None,
                min_value=None,
                units="reflectance",
                scale_factor=None,
                offset=None,
                mean_value=None,
                number_of_values=None,
                standard_deviation=None,
                other_property_type=None,
                other_property=None,
                bits_per_value=32,
                range_element_description=None,
                bound_max=None,
                bound_min=None,
                bound_units=None,
                peak_response=None,
                tone_gradation=None
            )
            bands.append(band)
        
        return bands
    
    def create_classes(self) -> List[NamedValue]:
        """Create class definitions"""
        return [
            NamedValue(key="background", value="Background pixels (non-burn areas)"),
            NamedValue(key="burn_scar", value="Burn scar pixels")
        ]
    
    def extract_date_from_tile_id(self, tile_id: str) -> str | None:
        """
        Extract date from tile ID
        Format: T10SDH.2020248.v1.4 -> 2020-09-04 (day 248 of 2020)
        """
        try:
            # Extract year and day of year
            parts = tile_id.split(".")
            if len(parts) >= 2:
                date_part = parts[1]
                if len(date_part) >= 7:
                    year = date_part[:4]
                    day_of_year = date_part[4:7]
                    # Convert day of year to approximate date (simplified)
                    # This is a rough approximation - for exact dates you'd need proper conversion
                    return f"{year}-{day_of_year}"
        except:
            pass
        return None
    
    def create_training_data(self, tile_ids: Dict[str, List[str]]) -> List[AI_EOTrainingData]:
        """Create training data objects for all tile IDs"""
        td_list = []
        
        for split, ids in tile_ids.items():
            print(f"Processing {split} split: {len(ids)} tiles")
            
            for tile_id in ids:
                merged_name = f"subsetted_512x512_HLS.S30.{tile_id}_merged.tif"
                mask_name = f"subsetted_512x512_HLS.S30.{tile_id}.mask.tif"
                
                # Create pixel label for semantic segmentation
                pixel_label = AI_PixelLabel(
                    type="AI_PixelLabel",
                    image_url=[f"{self.base_url}/{split}/{mask_name}"],
                    image_format=["image/tiff"],
                    is_negative=False,
                    confidence=1.0
                )
                
                # Skip date parsing for now to avoid validation issues
                data_time = None
                
                td = AI_EOTrainingData(
                    type="AI_EOTrainingData",
                    id=f"{split}_{tile_id}",
                    data_url=[f"{self.base_url}/{split}/{merged_name}"],
                    labels=[pixel_label],
                    extent=self.extent,
                    data_time=data_time
                )
                td_list.append(td)
        
        return td_list
    
    def create_task(self) -> AI_EOTask:
        """Create the semantic segmentation task"""
        return AI_EOTask(
            type="AI_EOTask",
            id="hls_burn_scars_semantic_segmentation",
            task_type="Semantic Segmentation"
        )
    
    def create_dataset(self, td_list: List[AI_EOTrainingData]) -> EOTrainingDataset:
        """Create the complete dataset object"""
        return EOTrainingDataset(
            type="AI_EOTrainingDataset",
            id="hls_burn_scars",
            name="HLS Burn Scars Semantic Segmentation Dataset",
            description="High-resolution satellite imagery and burn scar masks for training semantic segmentation models. "
                       "Dataset contains HLS S30 multispectral imagery with corresponding binary masks indicating burn scar areas. "
                       "Images are 512x512 pixels with 30m resolution in UTM Zone 10N projection. "
                       f"Total dataset size: {len(td_list)} image-mask pairs.",
            license="CC-BY-4.0",  # Update with actual license
            tasks=[self.create_task()],
            data=td_list,
            classes=self.create_classes(),
            bands=self.create_bands(),
            extent=self.extent,
            image_size=f"{self.image_size[0]}x{self.image_size[1]}",
            amount_of_training_data=len(td_list),
            number_of_classes=len(self.classes),
            keywords=["remote sensing", "satellite imagery", "burn scars", "wildfire", "semantic segmentation", "HLS", "Landsat", "multispectral"],
            providers=["NASA", "USGS"],
            version="1.0",
            created_time="2024-01-01",  # Update with actual creation date
            updated_time="2024-01-01"   # Update with actual update date
        )
    
    def generate_tdml(self, output_file: str = "hls_burn_scars_complete_tdml.json", 
                     gitattributes_path: str = ".gitattributes") -> None:
        """Generate complete TDML metadata from .gitattributes file"""
        print(" Discovering tile IDs from .gitattributes...")
        tile_ids = self.parse_gitattributes(gitattributes_path)
        
        total_tiles = sum(len(ids) for ids in tile_ids.values())
        print(f" Found {total_tiles} total tile IDs:")
        for split, ids in tile_ids.items():
            print(f"   {split}: {len(ids)} tiles")
        
        print(" Creating training data objects...")
        td_list = self.create_training_data(tile_ids)
        
        print("  Creating dataset...")
        dataset = self.create_dataset(td_list)
        
        print(" Writing TDML to JSON...")
        write_to_json(dataset, output_file)
        
        print(f" Generated TDML for {len(td_list)} training data items")
        print(f" Output saved to: {output_file}")
        
        # Print summary statistics
        print("\n  Dataset Summary:")
        print(f"   Total samples: {len(td_list)}")
        print(f"   Classes: {len(self.classes)}")
        print(f"   Bands: {len(self.create_bands())}")
        print(f"   Image size: {self.image_size[0]}x{self.image_size[1]} pixels")
        print(f"   Resolution: {self.resolution[0]}x{self.resolution[1]} meters")
        print(f"   CRS: {self.crs}")
        print(f"   Estimated size: ~{len(td_list) * 6.5:.1f} MB")
        
        # Print sample tile IDs for verification
        print("\n Sample tile IDs:")
        for split, ids in tile_ids.items():
            print(f"   {split}: {ids[:3]}..." if len(ids) > 3 else f"   {split}: {ids}")

def main():
    """Main function to generate TDML from .gitattributes"""
    generator = HLSBurnScarsCompleteTDMLGenerator()
    
    # Generate TDML using .gitattributes file
    generator.generate_tdml("hls_burn_scars_tdml.json", ".gitattributes")

if __name__ == "__main__":
    main()
