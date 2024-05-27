import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple, List

try:
    from picox.compiler import compile_file_to_command
except ImportError as err:
    COMPILER_IMPORTED = False
    COMPILER_ERROR = err
else:
    COMPILER_IMPORTED = True
    COMPILER_ERROR = None

class CompiledCommand(NamedTuple):
    command_str: str
    params: List[str]
    file_path: Path


def extract_parameters(text):
    pattern = r'\{([^{}]+)\}(?![^{]*\})'
    return re.findall(pattern, text)

def compile_file(input_file_path):
    with input_file_path.open() as input_file_fp:
        command_str = compile_file_to_command(input_file_fp)
        params = extract_parameters(command_str)
    return CompiledCommand(command_str, params, input_file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compile raw commands into compiled files to use for picox')
    parser.add_argument('file_path', type=Path, help='Path to the file or directory to process')
    parser.add_argument('output_file', type=Path, help='Path to output file where the results will be stored')
    parser.add_argument('--generate-stub', 
                        action="store_true", 
                        default=False, 
                        required=False, 
                        help="If you've messed up your compiled commands file, \
                            this will generate stubbed functions to get you over that \
                            to do a full compile again")

    args = parser.parse_args()
    compiled_commands = []

    if not COMPILER_IMPORTED and not args.generate_stub:
        print(f"Could not import picox correctly: {COMPILER_ERROR}")
        print(f"Chances are, you messed up the compiled commands in the package. run this with --generate-stub with the raw_commands directory!")
        sys.exit(2)


    if not args.file_path:
        print("No path provided")
        sys.exit(1)

    if not args.file_path.exists():
        print("The provided path does not exist")
        sys.exit(1)

    if args.file_path.is_dir():
        files_to_process = args.file_path.iterdir()
    elif args.file_path.is_file():
        files_to_process = [args.file_path]
    else:
        print("Invalid file or directory path")
        sys.exit(1)

    for file_path in files_to_process:
        if file_path.is_file():  # Check each path if it's a file
            if args.generate_stub:
                compiled_commands.append(CompiledCommand("", [], file_path))
            else:
                compiled_commands.append(compile_file(file_path))


    # Create output file contents
    output_lines = []
    output_lines.append(f"# Auto-generated with compile.py at {datetime.now(timezone.utc)}")
    for compiled_command in compiled_commands:
        output_lines.append("")
        output_lines.append(f"# {compiled_command.file_path}")
        output_lines.append(f"{compiled_command.file_path.stem} = lambda {', '.join(compiled_command.params)} : f\"{compiled_command.command_str}\"")

    # Write output to file specified by output_file
    try:
        with args.output_file.open('w') as output_fp:
            output_fp.write("\n".join(output_lines))
    except (IsADirectoryError, FileNotFoundError, OSError, IOError) as err:
        print(f"Unable to save compiled commands: {err}")
    print(f"Output written to {args.output_file}")
