# Download Papers - Instructions

## Quick Start

1. **Install required dependencies:**

```bash
cd ingestion
pip install -r requirements.txt
```

2. **Run the download script:**

```bash
python download_papers.py --yes
```

The script will:

- Read arXiv IDs from `pending_papers.json` (100 papers)
- Download PDFs to `data/` directory using **parallel processing**
- Skip files that already exist
- Show progress and summary
- Use multiple threads for fast downloads (CPU count × 2)

## What the Script Does

1. **Extracts arXiv IDs** from `pending_papers.json` (JSON file with paper metadata)

2. **Downloads PDFs in parallel** from arXiv using multiple URL formats:

   - `https://arxiv.org/pdf/{id}.pdf`
   - `https://arxiv.org/pdf/{id}v1.pdf`
   - `https://arxiv.org/pdf/hep-th/{id}.pdf`
   - `https://arxiv.org/pdf/hep-ph/{id}.pdf`
   - Version-specific URLs if needed

3. **Saves files** to `data/` directory with proper naming (e.g., `1110.2569v3.pdf`)

4. **Verifies downloads** by checking:

   - File size (> 1KB)
   - Valid PDF header (`%PDF`)

5. **Provides summary** of successful downloads, skipped files, and failures

6. **Uses parallel processing** - Downloads multiple papers simultaneously for faster processing

## Example Output

```
Reading papers from JSON file: pending_papers.json
Found 100 unique arXiv papers to download

================================================================================
Downloading 100 papers from arXiv
Output directory: data
Using 24 parallel threads
================================================================================

[1/100] ✓ arXiv:9510169 - Downloaded: 9510169v1.pdf
[2/100] ✓ arXiv:9602052 - Downloaded: 9602052v2.pdf
[3/100] ✓ arXiv:9503124 - Already exists: 9503124v2.pdf
...

================================================================================
Download Summary
================================================================================
Successfully downloaded: 53
Skipped (already exists): 47
Failed: 0
```

## Command-Line Options

```bash
# Use custom JSON file
python download_papers.py --json-file custom_papers.json --yes

# Use custom output directory
python download_papers.py --output-dir custom_folder --yes

# Interactive mode (prompts for confirmation)
python download_papers.py
```

## Manual Download (if script fails)

If some papers fail to download, you can download them manually:

```bash
# Example for paper arXiv:9806072
cd ingestion/data
wget https://arxiv.org/pdf/9806072.pdf -O 9806072.pdf

# Or using curl
curl "https://arxiv.org/pdf/9806072.pdf" -o 9806072.pdf
```

## After Downloading

Once all papers are downloaded, run the ingestion pipeline:

```bash
cd ingestion

# Step 1: Extract text from PDFs
python extract_pdfs.py

# Step 2: Chunk and generate embeddings
python chunk_and_embed.py

# Step 3: Upload to Pinecone
python upload_to_pinecone.py
```
