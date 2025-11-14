# Download Papers - Instructions

## Quick Start

1. **Install required dependency:**

```bash
pip install requests
```

2. **Run the download script:**

```bash
python download_papers.py
```

The script will:

- Read arXiv IDs from `pending_papers.json`
- Download PDFs to `data/papers/` directory
- Skip files that already exist
- Show progress and summary
- Be respectful to arXiv servers (1.5s delay between downloads)

## What the Script Does

1. **Extracts arXiv IDs** from `pending_papers.json` (looks for patterns like `arXiv:9806072` or `arXiv:1503.06237`)

2. **Downloads PDFs** from arXiv using multiple URL formats:

   - `https://arxiv.org/pdf/{id}.pdf`
   - `https://arxiv.org/pdf/{id}v1.pdf`
   - And version-specific URLs if needed

3. **Saves files** to `data/papers/` directory with proper naming

4. **Verifies downloads** by checking:

   - File size (> 1KB)
   - Valid PDF header (`%PDF`)

5. **Provides summary** of successful downloads, skipped files, and failures

## Example Output

```
================================================================================
Downloading 40 papers from arXiv
Output directory: data/papers
================================================================================

[1/40] Downloading arXiv:9806072... ✓ Downloaded: 9806072.pdf
[2/40] Downloading arXiv:9802150... ✓ Already exists: 9802150v2.pdf
[3/40] Downloading arXiv:9905104... ✓ Downloaded: 9905104.pdf
...

================================================================================
Download Summary
================================================================================
Successfully downloaded: 35
Skipped (already exists): 3
Failed: 2
```

## Manual Download (if script fails)

If some papers fail to download, you can download them manually:

```bash
# Example for paper arXiv:9806072
wget https://arxiv.org/pdf/9806072.pdf -O data/papers/9806072.pdf

# Or using curl
curl "https://arxiv.org/pdf/9806072.pdf" -o data/papers/9806072.pdf
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

## Troubleshooting

**Error: "No module named 'requests'"**

```bash
pip install requests
```

**Some papers fail to download:**

- Check your internet connection
- Verify the arXiv ID is correct
- Try downloading manually using the URLs shown in the error message
- Some older papers might have different URL formats

**Script is too slow:**

- The 1.5s delay is to be respectful to arXiv servers
- You can modify the `delay` parameter in the script if needed
- But be careful not to overload their servers
