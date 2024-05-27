import token
import tokenize
import re
from io import StringIO
from typing import IO, Union

from .upy import FAILED_MARKER


def replace_braces(match) -> str:
    """
    Fixup curly braces within an f-string by doubling them. This stops them from being interpreted
    as an argument to the raw command
    Args:
        match (str) : Matched f-string
    returns:
        str
    """
    # Before and after are the quotes that will remain unchanged
    before, f_content, after = match.groups()
    # Replace the curly braces in the f-string content
    modified_content = re.sub(r'(?<!\{)\{(?!\{)', '{{', f_content)
    modified_content = re.sub(r'(?<!\})\}(?!\})', '}}', modified_content)
    return f'{before}{modified_content}{after}'

def fix_fstring_braces(source: str):
    """
    Pass in a string
    """
    # Regex to match an f-string
    f_string_pattern = r'(f[rfb]?[\'"])(.*?)([\'"])'

    # Use re.sub with the replace function to modify the code
    modified_code = re.sub(f_string_pattern, replace_braces, source, flags=re.DOTALL)
    return modified_code

def remove_comments(source: Union[IO[bytes], str]):
    """
    Removes comments from Python source code while attempting to preserve line structure.

    Parameters:
    source (str or file): A string containing Python code or a file-like object to read from.

    Returns:
    str: The Python code with comments removed.
    """
    # Handling the input source: can be a string or a file-like object
    if isinstance(source, str):
        source = StringIO(source)
    
    cleaned_code = ""
    previous_token_type = token.INDENT  # Previous token type, initially set to INDENT
    last_line_number = -1  # Last line number processed
    last_column = 0  # Last column number processed

    # Token generator from the source
    tokgen = tokenize.generate_tokens(source.readline)
    for token_type, token_text, (start_line, start_col), (end_line, end_col), line_text in tokgen:
        if start_line > last_line_number:
            last_column = 0  # Reset column for a new line
        if start_col > last_column:
            cleaned_code += " " * (start_col - last_column)  # Add necessary spaces for alignment

        # Handle different types of tokens
        if token_type == token.STRING and (previous_token_type == token.INDENT or previous_token_type == token.NEWLINE):
            cleaned_code += token_text  # Include strings (possible docstrings are treated as code)
        elif token_type != tokenize.COMMENT:
            cleaned_code += token_text  # Add the text of non-comment tokens
        
        # Update previous token type, column and line number
        previous_token_type = token_type
        last_column = end_col
        last_line_number = end_line

    return cleaned_code

def fix_lines(source: Union[IO[bytes], str]):
    """
    Read a file line by line, stripping existing line endings and appending '\n' to each line.
    Also performs a one level indent to all lines
    Removes empty lines
    
    Args:
        source (str): source file to modify
    
    Returns:
        str: The content of the file with uniformly normalized line endings.
    """

    if isinstance(source, str):
        source = StringIO(source)

    normalized_lines = []

    # Read each line, strip off the line ending and append '\n'
    for line in source:
        if (line := line.rstrip('\r\n') + '\\\\n') != "\\\\n":
            normalized_lines.append(f"    {line}")
    
    # Join all the lines to form the full content
    normalized_content = ''.join(normalized_lines)
    
    return normalized_content

def compile_file_to_command(file_data: Union[IO[bytes], str]) -> str:
    """
    Compiles an open file in "r" mode into a str which is a one line lambda function of the entire file
    The resulting function from the file wraps the script in a try/except with known failure marker and
    an `exec()`. This function correctly escapes quotes, f-string curly brackets, strips newlines and fixes
    line endings
    Args:
        file_data (IO[bytes]) : file pointer to script to compile into a wrapped lambda
    """
    if isinstance(file_data, str):
        file_data = StringIO(file_data)
    raw_command = file_data.read()

    raw_command = remove_comments(raw_command)
    raw_command = fix_fstring_braces(raw_command)
    raw_command = fix_lines(raw_command)

    # Escape any quotes
    raw_command = raw_command.replace("\"", "\\\\\\\"")
    raw_command = raw_command.replace("\'", "\\\\\\\'")

    # wrap a try catch with known failure marker
    raw_command = f"try:\\\\n{raw_command}\\\\nexcept Exception as e:\\\\n    print(f\\\\\\\"{{{{str(e)}}}}{FAILED_MARKER}\\\\\\\")"

    # wrap in exec
    raw_command = f"exec(\'{raw_command}\')"

    return raw_command

