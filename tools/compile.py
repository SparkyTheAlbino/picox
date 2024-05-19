import re
from datetime import datetime, timezone
from pathlib import Path

from picox.compiler import compile_file_to_command

RAW_COMMANDS_DIR = "./src/raw_commands/"
OUTPUT_FILE = "./src/picox/commands/compiled.py"

def extract_parameters(text):
    pattern = r'\{([^{}]+)\}(?![^{]*\})'
    return re.findall(pattern, text)

if __name__ == "__main__":
    output_lines = []
    output_lines.append(f"# Auto-generated with compile.py at {datetime.now(timezone.utc)}")

    raw_commands_dir = Path(RAW_COMMANDS_DIR)
    output_file = Path(OUTPUT_FILE)

    # Get all files in the raw_commands dir and loop through compiling them
    for raw_command_file in raw_commands_dir.iterdir():
        with raw_command_file.open() as raw_command_fp:
            result = compile_file_to_command(raw_command_fp)
            params = extract_parameters(result)
            output_lines.append("")
            output_lines.append(f"# {raw_command_file}")
            output_lines.append(f"{raw_command_file.stem} = lambda {", ".join(params)} : f\"{result}\"")

    # Output file
    with output_file.open("w") as output_file_fp:
        output_file_fp.write("\n".join(output_lines))

    print("Compile complete!")