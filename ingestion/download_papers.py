"""
Download arXiv Papers Script
Downloads PDF papers from arXiv based on the pending_papers.json file
"""

import re
import requests
import threading
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

# arXiv download URLs
BASE_URLS = ["https://arxiv.org/pdf", "https://arxiv.org/pdf/hep-th", "https://arxiv.org/pdf/hep-ph"]

# Directory and file defaults
DEFAULT_PAPERS_DIR = "data"
DEFAULT_LIST_FILE = "pending_papers.json"

# Download configuration
DEFAULT_VERSION = "v1"
OLD_FORMAT_LENGTH = 7
DEFAULT_TIMEOUT = 30
DOWNLOAD_CHUNK_SIZE = 8192
MIN_PDF_SIZE_BYTES = 1000
PDF_MAGIC_BYTES = b'%PDF'

# HTTP configuration
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Threading configuration
DEFAULT_CPU_COUNT = 4
WORKER_MULTIPLIER = 2

# User interaction
CONFIRMATION_RESPONSE = "y"

class ArxivDownloader:
    def __init__(self, papers_dir: str = DEFAULT_PAPERS_DIR, list_file: str = DEFAULT_LIST_FILE):
        self.papers_dir = Path(papers_dir)
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        self.list_file = Path(list_file)
        # Thread-safe lock for printing
        self.print_lock = threading.Lock()
        # Counter for progress tracking
        self.completed_count = 0
        self.total_count = 0
        
    def extract_arxiv_ids_from_json(self, json_file: str) -> List[str]:
        """Extract arXiv IDs from a JSON file with paper metadata"""
        json_path = Path(json_file)
        if not json_path.exists():
            print(f"Error: {json_file} not found!")
            return []
        
        arxiv_ids = []
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                papers = json.load(f)
                
            if isinstance(papers, list):
                for paper in papers:
                    if isinstance(paper, dict) and 'arxiv_id' in paper:
                        arxiv_ids.append(paper['arxiv_id'])
                    elif isinstance(paper, str):
                        arxiv_ids.append(paper)
            
            # Remove duplicates and sort
            arxiv_ids = list(set(arxiv_ids))
            arxiv_ids.sort()
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            return []
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return []
        
        return arxiv_ids
    
    def normalize_arxiv_id(self, arxiv_id: str) -> Tuple[str, str]:
        """
        Normalize arXiv ID and return both the ID and filename
        arXiv IDs can be: 9806072, 1503.06237, etc.
        """
        # Remove any version suffix if present
        arxiv_id_clean = arxiv_id.split('v')[0]
        
        # Format for URL (keep dots as-is for newer IDs)
        url_id = arxiv_id_clean
        
        # Format for filename (replace dots with nothing for older format, keep for newer)
        if '.' in arxiv_id_clean:
            # New format: 1503.06237 -> 1503.06237
            filename = arxiv_id_clean
        else:
            # Old format: 9806072 -> 9806072
            filename = arxiv_id_clean
        
        return url_id, filename
    
    def get_arxiv_urls(self, arxiv_id: str) -> List[str]:
        """
        Generate possible arXiv PDF URLs for all base URLs and cases
        Handles: with/without version, old format (7 digits) vs new format (YYYY.NNNNN)
        """
        url_id, filename = self.normalize_arxiv_id(arxiv_id)
        urls = []
        
        # Check if original ID had a version number
        has_version = 'v' in arxiv_id
        version = arxiv_id.split('v')[1] if has_version else None
        
        # Generate URLs for each base URL
        for base_url in BASE_URLS:
            # Case 1: Without version suffix
            urls.append(f"{base_url}/{url_id}.pdf")
            
            # Case 2: With version suffix (if original had one)
            if has_version and version:
                urls.append(f"{base_url}/{url_id}v{version}.pdf")
            
            # Case 3: Try with v1 (common default version)
            urls.append(f"{base_url}/{url_id}{DEFAULT_VERSION}.pdf")
            
            # Case 4: For old format (7 digits), try without leading zeros variations
            if len(url_id) == OLD_FORMAT_LENGTH and not '.' in url_id:
                # Some old papers might be accessed differently
                urls.append(f"{base_url}/{url_id[:2]}/{url_id[2:]}.pdf")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _create_session(self) -> requests.Session:
        """Create a new requests session for a thread"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': USER_AGENT
        })
        return session
    
    def download_paper(self, arxiv_id: str) -> Tuple[bool, str, int]:
        """
        Download a paper from arXiv
        Returns: (success, message, index)
        Note: Each thread gets its own session for thread safety
        """
        # Create a session for this thread
        session = self._create_session()
        url_id, filename = self.normalize_arxiv_id(arxiv_id)
        
        # Check if file already exists (thread-safe file check)
        existing_files = list(self.papers_dir.glob(f"{filename}*.pdf"))
        if existing_files:
            return True, f"Already exists: {existing_files[0].name}", 0
        
        # Try different URL formats
        urls = self.get_arxiv_urls(arxiv_id)
        
        for url in urls:
            try:
                response = session.get(url, timeout=DEFAULT_TIMEOUT, stream=True)
                
                if response.status_code == 200:
                    # Check if it's actually a PDF
                    content_type = response.headers.get('content-type', '')
                    if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                        continue
                    
                    # Determine filename (try to get from Content-Disposition or use arxiv_id)
                    content_disposition = response.headers.get('content-disposition', '')
                    if 'filename=' in content_disposition:
                        downloaded_filename = re.findall(r'filename="?([^"]+)"?', content_disposition)[0]
                    else:
                        # Use the arxiv ID as filename
                        downloaded_filename = f"{filename}.pdf"
                    
                    filepath = self.papers_dir / downloaded_filename
                    
                    # Download the file
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                            f.write(chunk)
                    
                    # Verify it's a valid PDF
                    if filepath.stat().st_size > MIN_PDF_SIZE_BYTES:  # At least 1KB
                        with open(filepath, 'rb') as f:
                            if f.read(4) == PDF_MAGIC_BYTES:
                                session.close()
                                return True, f"Downloaded: {downloaded_filename}", 0
                    
                    # If invalid, delete and try next URL
                    filepath.unlink()
                    
            except requests.exceptions.RequestException as e:
                continue
            except Exception as e:
                continue
        
        session.close()
        return False, f"Failed to download (tried {len(urls)} URLs)", 0
    
    def _download_with_progress(self, arxiv_id: str, index: int) -> Tuple[str, bool, str]:
        """Wrapper for download_paper that tracks progress"""
        success, message, _ = self.download_paper(arxiv_id)
        
        # Thread-safe progress update
        with self.print_lock:
            self.completed_count += 1
            status = "✓" if success else "✗"
            print(f"[{self.completed_count}/{self.total_count}] {status} arXiv:{arxiv_id} - {message}")
        
        return arxiv_id, success, message
    
    def download_all(self, arxiv_ids: List[str] = None, max_workers: int = None):
        """
        Download all papers from the list in parallel
        max_workers: Number of parallel threads (default: CPU count * 2 for I/O-bound tasks)
        """
        if arxiv_ids is None:
            arxiv_ids = self.extract_arxiv_ids_from_json(str(self.list_file))
        
        if not arxiv_ids:
            print("No arXiv IDs found!")
            return
        
        # Determine number of workers (use CPU count * 2 for I/O-bound downloads)
        if max_workers is None:
            import os
            max_workers = min(len(arxiv_ids), (os.cpu_count() or DEFAULT_CPU_COUNT) * WORKER_MULTIPLIER)
        
        self.total_count = len(arxiv_ids)
        self.completed_count = 0
        
        print("=" * 80)
        print(f"Downloading {len(arxiv_ids)} papers from arXiv")
        print(f"Output directory: {self.papers_dir}")
        print(f"Using {max_workers} parallel threads")
        print("=" * 80)
        print()
        
        results = {
            'success': [],
            'skipped': [],
            'failed': []
        }
        
        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_id = {
                executor.submit(self._download_with_progress, arxiv_id, i): arxiv_id
                for i, arxiv_id in enumerate(arxiv_ids, 1)
            }
            
            # Process completed downloads as they finish
            for future in as_completed(future_to_id):
                arxiv_id, success, message = future.result()
                
                if success:
                    if "Already exists" in message:
                        results['skipped'].append(arxiv_id)
                    else:
                        results['success'].append(arxiv_id)
                else:
                    results['failed'].append(arxiv_id)
        
        # Print summary
        print()
        print("=" * 80)
        print("Download Summary")
        print("=" * 80)
        print(f"Successfully downloaded: {len(results['success'])}")
        print(f"Skipped (already exists): {len(results['skipped'])}")
        print(f"Failed: {len(results['failed'])}")
        
        if results['failed']:
            print()
            print("Failed papers:")
            for arxiv_id in results['failed']:
                print(f"  - arXiv:{arxiv_id}")
            print()
            print("You can try downloading these manually:")
            for arxiv_id in results['failed']:
                url_id, _ = self.normalize_arxiv_id(arxiv_id)
                print(f"  wget https://arxiv.org/pdf/{url_id}.pdf -O {self.papers_dir}/{arxiv_id}.pdf")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Download arXiv papers from pending_papers.json file'
    )
    parser.add_argument(
        '--json-file',
        type=str,
        default=None,
        help=f'Path to JSON file containing paper metadata (default: {DEFAULT_LIST_FILE})'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=DEFAULT_PAPERS_DIR,
        help=f'Output directory for downloaded PDFs (default: {DEFAULT_PAPERS_DIR})'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt and proceed with download'
    )
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = ArxivDownloader(
        papers_dir=args.output_dir,
        list_file=DEFAULT_LIST_FILE
    )
    
    # Extract arXiv IDs from JSON file (default: pending_papers.json)
    json_file = args.json_file if args.json_file else DEFAULT_LIST_FILE
    print(f"Reading papers from JSON file: {json_file}")
    arxiv_ids = downloader.extract_arxiv_ids_from_json(json_file)
    
    if not arxiv_ids:
        print("No arXiv IDs found!")
        print("Please ensure the file exists and contains valid arXiv IDs")
        return
    
    print(f"Found {len(arxiv_ids)} unique arXiv papers to download")
    print()
    
    # Ask for confirmation unless --yes flag is set
    if not args.yes:
        response = input("Proceed with download? (y/n): ").strip().lower()
        if response != CONFIRMATION_RESPONSE:
            print("Download cancelled.")
            return
    
    # Download all papers in parallel
    # Uses all available CPU cores * 2 (for I/O-bound tasks)
    downloader.download_all(arxiv_ids)


if __name__ == "__main__":
    main()

