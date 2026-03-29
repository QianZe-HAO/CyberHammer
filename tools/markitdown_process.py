from markitdown import MarkItDown
from pathlib import Path


class MarkItDownProcessor:

    def __init__(self, enable_plugins=False):
        self.md = MarkItDown(enable_plugins=enable_plugins)

    def process(self, input_path: str):
        input_path = Path(input_path)
        output_path = input_path.with_suffix(".md")
        result = self.md.convert(str(input_path))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)

        return output_path
