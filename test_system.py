#!/usr/bin/env python3
"""
Test script for KMRL Knowledge Engine components
"""
import os
import sys

# Set working directory to script location
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.append('.')

from src.document_processor import DocumentProcessor
from src.advanced_search import AdvancedSearch
from src.data_integration import UnifiedNamespaceSimulator, MaximoSimulator
from src.email_integration import EmailIntegration

def test_document_processing():
    """Test document processing capabilities"""
    print("=== Testing Document Processing ===")

    processor = DocumentProcessor()

    # Test with safety bulletin
    with open('data/sample_docs/safety_bulletin.txt', 'rb') as f:
        content = f.read()

    text = processor.extract_fulltext(content, '.txt')
    print(f"Extracted text length: {len(text)}")
    print(f"First 200 chars: {repr(text[:200])}...")

    meta = processor.extract_metadata('safety_bulletin.txt', content)
    print(f"Language detected: {meta['language']}")
    print(f"Document type: {meta['doc_type']}")
    print(f"Is bilingual: {meta.get('is_bilingual', False)}")

    quick = processor.quick_skim(content, meta)
    print(f"Extracted bullets: {len(quick['bullets'])}")
    print(f"Extracted risks: {len(quick['risks'])}")

def test_advanced_search():
    """Test advanced search capabilities"""
    print("\n=== Testing Advanced Search ===")

    search = AdvancedSearch()

    # Index sample documents
    processor = DocumentProcessor()

    for filename in os.listdir('data/sample_docs'):
        if filename.endswith('.txt'):
            with open(f'data/sample_docs/{filename}', 'rb') as f:
                content = f.read()

            text = processor.extract_fulltext(content, '.txt')
            meta = processor.extract_metadata(filename, content)
            search.index_document(filename, filename, text, meta)

    # Test full-text search
    results = search.full_text_search("safety")
    print(f"Full-text search results: {len(results)}")

    # Test semantic search
    results = search.semantic_search("maintenance procedures")
    print(f"Semantic search results: {len(results)}")

    # Test hybrid search
    results = search.hybrid_search("emergency evacuation")
    print(f"Hybrid search results: {len(results)}")

def test_data_integration():
    """Test data integration components"""
    print("\n=== Testing Data Integration ===")

    # Test UNS
    uns = UnifiedNamespaceSimulator()
    assets = uns.get_all_assets()
    print(f"Assets in UNS: {len(assets)}")

    for asset_id, data in list(assets.items())[:2]:
        print(f"Asset {asset_id}: Status={data['status']}, Temp={data['temperature']:.1f}°C")

    # Test Maximo
    maximo = MaximoSimulator()
    work_orders = maximo.get_work_orders()
    print(f"Work orders: {len(work_orders)}")

    for wo in work_orders:
        print(f"WO {wo['wo_id']}: {wo['description']} - {wo['status']}")

def test_email_integration():
    """Test email integration (without sending)"""
    print("\n=== Testing Email Integration ===")

    email = EmailIntegration()
    if email.email_ready:
        print("Email integration configured")
    else:
        print("Email integration not configured (set environment variables)")

if __name__ == "__main__":
    test_document_processing()
    test_advanced_search()
    test_data_integration()
    test_email_integration()
    print("\n=== All tests completed ===")