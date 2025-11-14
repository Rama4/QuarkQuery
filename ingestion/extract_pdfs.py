"""
PDF Text Extraction Script for Physics Papers
Extracts text, symbols, and metadata from physics papers for RAG pipeline
"""

import fitz  # PyMuPDF
import json
import os
from pathlib import Path
from typing import Dict, List
import re


class PDFExtractor:
    def __init__(self, papers_dir: str = "../data/papers", output_dir: str = "extracted_data"):
        self.papers_dir = Path(papers_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path: Path) -> Dict:
        """
        Extract text and metadata from a single PDF file
        """
        print(f"Processing: {pdf_path.name}")
        
        doc = fitz.open(pdf_path)
        
        extracted_data = {
            "filename": pdf_path.name,
            "arxiv_id": self._extract_arxiv_id(pdf_path.name),
            "num_pages": len(doc),
            "metadata": {},
            "full_text": "",
            "pages": []
        }
        
        # Extract metadata
        extracted_data["metadata"] = doc.metadata
        
        # Extract text from each page
        full_text = []
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            
            # Clean up the text
            page_text = self._clean_text(page_text)
            
            extracted_data["pages"].append({
                "page_number": page_num,
                "text": page_text
            })
            
            full_text.append(page_text)
        
        extracted_data["full_text"] = "\n\n".join(full_text)
        
        doc.close()
        return extracted_data
    
    def _extract_arxiv_id(self, filename: str) -> str:
        """
        Extract arXiv ID from filename
        Example: 1110.2569v3.pdf -> 1110.2569v3
        """
        return filename.replace('.pdf', '')
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text while preserving mathematical symbols
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove page numbers that appear alone on a line
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        return text.strip()
    
    def extract_all_pdfs(self) -> List[Dict]:
        """
        Extract text from all PDFs in the papers directory
        """
        pdf_files = list(self.papers_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.papers_dir}")
            return []
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        all_extracted_data = []
        
        for pdf_file in pdf_files:
            try:
                extracted = self.extract_text_from_pdf(pdf_file)
                all_extracted_data.append(extracted)
                
                # Save individual JSON file
                output_file = self.output_dir / f"{extracted['arxiv_id']}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(extracted, f, indent=2, ensure_ascii=False)
                
                print(f"  ✓ Extracted {extracted['num_pages']} pages, {len(extracted['full_text'])} characters")
                
            except Exception as e:
                print(f"  ✗ Error processing {pdf_file.name}: {str(e)}")
                continue
        
        # Save combined data
        combined_file = self.output_dir / "all_papers.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successfully processed {len(all_extracted_data)} papers")
        print(f"✓ Saved to {self.output_dir}")
        
        return all_extracted_data
    
    def generate_summary_report(self, extracted_data: List[Dict]):
        """
        Generate a summary report of extracted papers
        """
        report_file = self.output_dir / "extraction_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PDF EXTRACTION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total papers processed: {len(extracted_data)}\n\n")
            
            for paper in extracted_data:
                f.write(f"\nPaper: {paper['filename']}\n")
                f.write(f"  arXiv ID: {paper['arxiv_id']}\n")
                f.write(f"  Pages: {paper['num_pages']}\n")
                f.write(f"  Characters: {len(paper['full_text']):,}\n")
                
                # Extract title from metadata if available
                if paper['metadata'].get('title'):
                    f.write(f"  Title: {paper['metadata']['title']}\n")
                
                # Show first 200 characters of text
                preview = paper['full_text'][:200].replace('\n', ' ')
                f.write(f"  Preview: {preview}...\n")
        
        print(f"✓ Summary report saved to {report_file}")


def main():
    print("=" * 80)
    print("Physics Papers PDF Extraction")
    print("=" * 80)
    print()
    
    extractor = PDFExtractor()
    extracted_data = extractor.extract_all_pdfs()
    
    if extracted_data:
        extractor.generate_summary_report(extracted_data)
        
        print("\n" + "=" * 80)
        print("Next Steps:")
        print("  1. Review extracted_data/ folder for JSON files")
        print("  2. Check extraction_report.txt for summary")
        print("  3. Ready for embedding generation and vector DB ingestion")
        print("=" * 80)


if __name__ == "__main__":
    main()

