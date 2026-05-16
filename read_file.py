read_tool = {"type": "function",
             "function":{
                 "name": "read_file",
                 "description": "Reads the content of a file and returns it as a string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path to the file to be read."
                            }
                        },
                        "required": ["file_path"]
                    }
             }}

def read_file(file_path):
    """Reads the content of a file and returns it as a string."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"
    

TOOL_MAPPING = {
    "read_file": read_file}