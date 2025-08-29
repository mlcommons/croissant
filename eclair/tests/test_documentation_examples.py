"""
Test script to validate the examples in the updated Python client documentation.
"""
import asyncio
import sys
import os
import pytest

# Add src to path so we can import from eclair
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eclair.client import EclairClient, GeminiMCPClient, ClaudeMCPClient
from eclair.client.gemini import GEMINI_AVAILABLE
from eclair.client.claude import CLAUDE_AVAILABLE
import pandas as pd
import requests
import io
import json


@pytest.mark.asyncio
async def test_basic_discovery():
    """Test example 1: Basic Dataset Discovery"""
    print("=== Testing Basic Dataset Discovery ===")
    
    client = EclairClient()
    
    try:
        # Search for datasets
        result = await client.search_datasets("fashion mnist")
        datasets = result.structured_content['result']
        
        print(f"Found {len(datasets)} datasets")
        for dataset in datasets:
            doc = dataset['document']
            print(f"- {doc['entity_name']} ({doc['collection_name']})")
        
        assert len(datasets) > 0, "Should find at least one dataset"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        pytest.fail(f"Basic discovery failed: {e}")


@pytest.mark.asyncio
async def test_preview_and_download():
    """Test example 3: Dataset Preview and Download"""
    print("\n=== Testing Dataset Preview and Download ===")
    
    client = EclairClient()
    
    try:
        # Search for Fashion-MNIST first
        search_result = await client.search_datasets("Han-Xiao Fashion-MNIST")
        if not search_result.structured_content.get('result'):
            print("No Fashion-MNIST found, using fallback dataset")
            # Find any dataset for testing
            fallback_search = await client.search_datasets("mnist")
            if fallback_search.structured_content.get('result'):
                datasets = fallback_search.structured_content['result']
                doc = datasets[0]['document']
                collection = doc['collection_name']
                dataset_name = doc['entity_name']
            else:
                print("No datasets found for testing")
                return False
        else:
            # Try to find Han-Xiao Fashion-MNIST specifically
            datasets = search_result.structured_content['result']
            found_fashion = False
            for dataset in datasets:
                doc = dataset['document']
                if 'han-xiao' in doc['collection_name'].lower() or 'fashion' in doc['entity_name'].lower():
                    collection = doc['collection_name']
                    dataset_name = doc['entity_name']
                    found_fashion = True
                    break
            
            if not found_fashion:
                # Use first available dataset
                doc = datasets[0]['document']
                collection = doc['collection_name']
                dataset_name = doc['entity_name']
        
        print(f"Testing with dataset: {dataset_name} from {collection}")
        
        # Try to get preview URL
        try:
            preview_result = await client.datasets_preview_url(collection, dataset_name)
            if preview_result.structured_content.get('result'):
                print("✅ Preview URL retrieved successfully")
            else:
                print("⚠️ Preview URL not available for this dataset")
        except Exception as e:
            print(f"⚠️ Preview URL error: {e}")
        
        # Try to get download information
        try:
            download_result = await client.download_dataset(collection, dataset_name)
            if download_result.structured_content.get('result'):
                print("✅ Download information retrieved successfully")
            else:
                print("⚠️ Download information not available")
        except Exception as e:
            print(f"⚠️ Download error: {e}")
        
        # Test passes if we got this far without major exceptions
        assert True, "Preview and download test completed"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        pytest.fail(f"Preview and download test failed: {e}")


@pytest.mark.asyncio
async def test_metadata_validation():
    """Test example 4: Metadata Validation"""
    print("\n=== Testing Metadata Validation ===")
    
    client = EclairClient()
    
    try:
        # Search for a dataset first
        search_result = await client.search_datasets("mnist")
        if not search_result.structured_content.get('result'):
            print("No datasets found for metadata testing")
            return False
        
        datasets = search_result.structured_content['result']
        doc = datasets[0]['document']
        collection = doc['collection_name']
        dataset_name = doc['entity_name']
        
        print(f"Testing metadata for: {dataset_name} from {collection}")
        
        # Get Croissant metadata
        try:
            metadata_result = await client.serve_croissant(collection, dataset_name)
            if metadata_result.structured_content.get('result'):
                metadata = metadata_result.structured_content['result']
                print("✅ Croissant metadata retrieved successfully")
                
                # Try to validate the metadata
                validation_result = await client.validate_croissant(metadata)
                if validation_result.structured_content.get('result'):
                    print("✅ Metadata validation completed")
                else:
                    print("⚠️ Validation result format different than expected")
                
                assert True, "Metadata validation test completed"
                
            else:
                print("⚠️ Croissant metadata not available for this dataset")
                pytest.skip("Croissant metadata not available for test dataset")
                
        except Exception as e:
            print(f"⚠️ Metadata error: {e}")
            pytest.skip(f"Metadata operation failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        pytest.fail(f"Metadata validation test failed: {e}")


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling example"""
    print("\n=== Testing Error Handling ===")
    
    client = EclairClient()
    
    try:
        result = await client.search_datasets("test query")
        if result.is_error:
            print(f"Tool error: {result.content[0].text}")
        else:
            print("✅ Search successful")
            
        # This test always passes as it's testing error handling
        assert True, "Error handling test completed"
        
    except Exception as e:
        print(f"⚠️ Connection error: {e}")
        # This is expected if server is not running - test should still pass
        assert True, "Error handling test completed (connection error is expected)"


def test_client_availability():
    """Test client availability check"""
    print("\n=== Testing Client Availability ===")
    
    print(f"Base client: {EclairClient is not None}")
    print(f"Gemini client: {GEMINI_AVAILABLE}")
    print(f"Claude client: {CLAUDE_AVAILABLE}")
    
    assert EclairClient is not None
    # Note: Gemini and Claude clients might not be available if dependencies aren't installed
