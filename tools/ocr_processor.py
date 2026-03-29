import os
import json
import re
import shutil

from .dots_ocr import DotsOCRParser


class OCRProcessor:
    def __init__(
        self,
        cache_folder="./cache",
        no_image=False,
        no_table=False,
        delete_cache=True,
    ):
        self.cache_folder = cache_folder
        self.no_image = no_image
        self.no_table = no_table
        self.delete_cache = delete_cache
        self.parser = DotsOCRParser(output_dir=self.cache_folder)

    def process(self, input_path: str, prompt_mode: str = "prompt_layout_all_en"):
        """Main method to process an image: OCR parsing + merge Markdown results."""
        # Paths setup
        output_md_folder = os.path.dirname(os.path.abspath(input_path))
        input_base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_subdir = os.path.join(self.cache_folder, input_base_name)
        ocr_result_jsonl_path = os.path.join(self.cache_folder, f"{input_base_name}.jsonl")
        merged_output_md = os.path.join(output_md_folder, f"{input_base_name}.md")

        print(f"OCR results will be saved to: {ocr_result_jsonl_path}")

        # Step 1: Perform OCR parsing
        print("Starting OCR parsing...")
        self.parser.parse_file(
            input_path=input_path,
            output_dir=self.cache_folder,
            prompt_mode=prompt_mode,
        )
        print(f"OCR parsing completed, results saved to: {self.cache_folder}")

        # Step 2: Merge Markdown files
        if not os.path.exists(ocr_result_jsonl_path):
            raise FileNotFoundError(f"OCR result file not found: {ocr_result_jsonl_path}")

        print("Starting to merge Markdown files...")
        md_paths = []
        with open(ocr_result_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    md_filename = data["md_content_nohf_path"].split("/")[-1]
                    full_path = os.path.join(output_subdir, md_filename)
                    md_paths.append(full_path)
                except Exception as e:
                    print(f"Failed to parse line: {e}")

        if not md_paths:
            raise ValueError("No Markdown file paths were generated.")

        # Regex patterns
        image_pattern = re.compile(r"!\[.*?\]\(.*?\)")
        table_pattern = re.compile(r"<table[^>]*>.*?</table>", re.DOTALL)

        # Merge into final Markdown
        with open(merged_output_md, "w", encoding="utf-8") as outfile:
            for md_path in md_paths:
                if not os.path.exists(md_path):
                    print(f"File does not exist: {md_path}")
                    continue
                try:
                    with open(md_path, "r", encoding="utf-8") as infile:
                        content = infile.read()

                        # Remove images if needed
                        if self.no_image:
                            content = image_pattern.sub("", content)

                        # Remove tables if needed
                        if self.no_table:
                            content = table_pattern.sub("", content)

                        outfile.write(content)
                        # outfile.write("\n\n")
                        # outfile.write("<hr>")
                        # outfile.write("\n\n")
                    print(f"Merged: {md_path}")
                except Exception as e:
                    print(f"Failed to read {md_path}: {e}")

        print(f"All files have been successfully merged into: {merged_output_md}")

        # Cleanup cache
        if os.path.exists(self.cache_folder) and self.delete_cache:
            shutil.rmtree(self.cache_folder)
            print(f"Folder '{self.cache_folder}' has been deleted.")
        else:
            print(f"Folder '{self.cache_folder}' does not exist or cleanup disabled.")

        return merged_output_md