"""Streamlit UI for document processing with OCR and MarkItDown"""

import streamlit as st
from tools import OCRProcessor, MarkItDownProcessor
from pathlib import Path
from dotenv import load_dotenv
import shutil


def markdown_convert_page():
    # Set page configuration
    st.set_page_config(
        page_title="Document to Markdown Processor",
        layout="wide",
    )

    st.title("Document Smart Conversion to Markdown")
    st.markdown(
        "Supports conversion of PDF, images (OCR), DOCX, PPTX, XLSX, and other files to Markdown"
    )

    # Load environment variables
    load_dotenv()

    NO_IMAGE = True
    NO_TABEL = False

    # Initialize processors
    @st.cache_resource
    def get_processors():
        ocr_processor = OCRProcessor(
            cache_folder="./cache",
            no_image=NO_IMAGE,
            no_table=NO_TABEL,
            delete_cache=True,
        )
        mid_processor = MarkItDownProcessor(enable_plugins=False)
        return ocr_processor, mid_processor

    ocr_processor, mid_processor = get_processors()

    # Temporary directories
    INPUT_DIR = Path("./input")
    OUTPUT_DIR = Path("./output")
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Clean up old files
    for dir_path in [INPUT_DIR, OUTPUT_DIR]:
        for f in dir_path.iterdir():
            if f.is_file():
                f.unlink()

    # File extension categories
    OCR_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png"}
    MID_EXTENSIONS = {".docx", ".pptx", ".xls", ".xlsx"}

    # === Sidebar: Model Info and Controls ===
    st.sidebar.header("Cyber Markdown")
    st.sidebar.markdown(
        f"""
    ### Model Information
    - **OCR Engine**: `Rednote DotsOCR`
    - **MarkItDown**: `DOCX/PPTX/XLSX to Markdown`
    - **No Image Output**: `{NO_IMAGE}`
    - **Table Extraction**: `{NO_TABEL}`
    """
    )

    if st.sidebar.button("Clear Cache and Output", width="stretch"):
        for d in [INPUT_DIR, OUTPUT_DIR, Path("./cache")]:
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
                d.mkdir(exist_ok=True)
        st.success("Cache and output have been cleared.")
        st.rerun()

    # === Main Area: Upload and Processing ===
    st.header("Upload Document")
    uploaded_file = st.file_uploader(
        "Select a document file (PDF, Image, DOCX, PPTX, XLSX, etc.)",
        type=["pdf", "jpg", "jpeg", "png", "docx", "pptx", "xls", "xlsx"],
        accept_multiple_files=False,  # ← 仅允许单个文件
    )

    if uploaded_file:
        st.write(
            f"Uploaded: `{uploaded_file.name}` ({uploaded_file.size // 1024 + 1} KB)"
        )

        if st.button("Start Processing", width="stretch"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Save uploaded file
                input_path: Path = INPUT_DIR / uploaded_file.name
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                status_text.text(f"Processing: {uploaded_file.name}")
                output_path = None

                # Determine type and process
                if input_path.suffix.lower() in OCR_EXTENSIONS:
                    st.info(f"Using OCR to process: {uploaded_file.name}")
                    output = ocr_processor.process(input_path=str(input_path))
                    if output:
                        output_path = Path(output)

                elif input_path.suffix.lower() in MID_EXTENSIONS:
                    st.info(f"Using MarkItDown to process: {uploaded_file.name}")
                    output = mid_processor.process(str(input_path))
                    if output:
                        output_path = Path(output)

                # Move output to result directory
                if output_path and output_path.exists():
                    final_dest = OUTPUT_DIR / output_path.name
                    if final_dest.exists():
                        final_dest.unlink()
                    shutil.move(str(output_path), final_dest)
                    result_msg = final_dest.name
                else:
                    result_msg = "Processing failed"

            except Exception as e:
                result_msg = f"Error: {str(e)}"

            progress_bar.progress(1.0)
            status_text.text("Processing complete.")

            # Display result
            st.subheader("Processing Result")
            st.write(f"`{uploaded_file.name}` → `{result_msg}`")

            # Provide download link if successful
            if result_msg != "Processing failed" and not result_msg.startswith("Error"):
                output_file = OUTPUT_DIR / result_msg
                with open(output_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        label=f"Download {result_msg}",
                        data=f.read(),
                        file_name=result_msg,
                        mime="text/markdown",
                        width="stretch",
                    )
    else:
        st.info("Please upload a file to begin processing.")
