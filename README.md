# Python implementation of building the primitives for an agent harness

This repo is a small workshop for building the basic pieces of an agent harness in Python.

It starts with one goal:

> Build a terminal chat loop where the model can ask your Python code to run a tool.

Right now, the project has:

- a terminal chat loop
- OpenRouter model calls
- message history
- one working tool: `read_file`

More tools will be added later. For now, the point is to understand the primitive mechanism before adding more moving parts.

## What this project is

An agent harness is the code around a language model that lets it do more than return text.

The model itself does not read files, edit files, run commands, or call APIs.

It can only request those actions.

Your Python code has to:

1. send the user message to the model
2. check whether the model wants to call a tool
3. read the tool name and arguments
4. run the matching Python function
5. append the tool result back into the message history
6. call the model again so it can answer using the tool result

That loop is the foundation.

## What you will build

The current version teaches the smallest useful version of tool calling:

```text
User asks a question
Model decides it needs a tool
Python runs the tool
Tool result goes back into messages
Model gives the final answer
```

The first tool is `read_file`.

That means you can ask something like:

```text
what is in example_text.txt
```

The model can request the `read_file` tool, your Python code reads the file, and the model uses the file contents to answer.

## The mental model

There are five important pieces:

```text
messages        = the conversation state
tools           = the list of tool schemas sent to the model
tool schema     = the description of a tool
Python function = the code that actually does the work
TOOL_MAPPING    = the router from tool name to Python function
```

The model sees the tool schema.

The model does not directly run your Python function.

Your code runs the function after the model requests the matching tool name.

A simple way to think about it:

```text
LLM             = decides what should happen next
tool schema     = tells the LLM what actions exist
TOOL_MAPPING    = connects tool names to real functions
Python function = performs the action
messages        = keeps the current conversation together
```

## Project structure

```text
.
├── main.py
├── chat.py
└── tools/
    ├── __init__.py
    └── read_file.py
```

## `main.py`

`main.py` is the entry point.

It should stay small.

Its job is only to start the chat loop.

```python
from chat import chat

def main():
    chat()

if __name__ == "__main__":
    main()
```

## `chat.py`

`chat.py` contains the main loop.

It is responsible for:

- reading input from the terminal
- appending user messages to `message_list`
- sending messages and tools to the model
- checking if the model requested a tool
- running the requested tool
- appending the tool result
- calling the model again
- printing the final assistant response

The important idea is that the chat loop does not stop at the first model response if the model asks for a tool.

It has to resolve the tool call first.

## `tools/read_file.py`

This file contains the first tool.

A tool has two parts:

1. a schema
2. a Python function

The schema describes the tool to the model.

The function does the actual work.

## The `read_file` function

The function is normal Python:

```python
def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read()
```

There is nothing special about this function by itself.

The model cannot call this function directly.

Your runtime calls it after the model requests the matching tool name.

## The tool schema

The schema tells the model that a tool exists.

```python
read_tool = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path of the file to read."
                }
            },
            "required": ["file_path"]
        }
    }
}
```

The model reads this and learns:

```text
There is a tool called read_file.
It reads a file.
It needs a file_path argument.
```

The schema name matters.

If the schema says:

```python
"name": "read_file"
```

then your tool mapping must also use:

```python
"read_file"
```

## `tools/__init__.py`

This file registers the available tools.

```python
from .read_file import read_tool, read_file

tools = [read_tool]

TOOL_MAPPING = {
    "read_file": read_file
}
```

There are two separate things here.

### `tools`

```python
tools = [read_tool]
```

This list is sent to the model.

It tells the model what tools it is allowed to request.

### `TOOL_MAPPING`

```python
TOOL_MAPPING = {
    "read_file": read_file
}
```

This dictionary is used by your Python code.

When the model asks for `"read_file"`, your code looks up that name in `TOOL_MAPPING` and finds the actual Python function.

The key must match the tool schema name.

This is correct:

```python
TOOL_MAPPING = {
    "read_file": read_file
}
```

This is wrong if the schema name is `"read_file"`:

```python
TOOL_MAPPING = {
    "read_tool": read_file
}
```

The Python variable name `read_tool` does not matter to the model.

The schema name does.

## How the chat loop works

The loop starts by reading input:

```python
user_input = input("User: ")
```

Then the user message is added to the message history:

```python
message_list.append({
    "role": "user",
    "content": user_input
})
```

Then the messages and tools are sent to the model:

```python
response = client.chat.send(
    model="minimax/minimax-m2.7",
    tools=tools,
    messages=message_list
)
```

At this point, the model can do one of two things.

It can answer normally:

```text
finish_reason = "stop"
```

Or it can ask for a tool:

```text
finish_reason = "tool_calls"
```

If it asks for a tool, your code has to run the tool before printing a final answer.

## Tool calling step by step

Suppose the user asks:

```text
what is in example_text.txt
```

The model might respond with a tool call like:

```json
{
  "name": "read_file",
  "arguments": {
    "file_path": "example_text.txt"
  }
}
```

Your code extracts the tool name:

```python
tool_name = tool_call.function.name
```

Then it parses the arguments:

```python
tool_args = json.loads(tool_call.function.arguments)
```

Now you have something like:

```python
tool_name = "read_file"

tool_args = {
    "file_path": "example_text.txt"
}
```

Then your code runs the matching function:

```python
tool_response = TOOL_MAPPING[tool_name](**tool_args)
```

This line is doing the routing.

It becomes:

```python
tool_response = TOOL_MAPPING["read_file"](
    file_path="example_text.txt"
)
```

Which becomes:

```python
tool_response = read_file(file_path="example_text.txt")
```

The result is then added back into the message history:

```python
message_list.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(tool_response)
})
```

Then the model is called again:

```python
response = client.chat.send(
    model="minimax/minimax-m2.7",
    tools=tools,
    messages=message_list
)
```

This second model call is required.

The model asked for the tool, but it does not know the result until your code sends the result back.

## The core loop

The important part of the agent harness is this:

```python
while response.choices[0].finish_reason == "tool_calls":
    assistant_message = response.choices[0].message

    message_list.append({
        "role": "assistant",
        "content": assistant_message.content,
        "tool_calls": assistant_message.tool_calls
    })

    for tool_call in assistant_message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        tool_response = TOOL_MAPPING[tool_name](**tool_args)

        message_list.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_response)
        })

    response = client.chat.send(
        model="minimax/minimax-m2.7",
        tools=tools,
        messages=message_list
    )
```

The loop means:

```text
While the model is asking for tools:
    run the requested tools
    append the tool results
    call the model again
```

Once the model stops asking for tools, print the final answer:

```python
print("Assistant:", response.choices[0].message.content)
```

## Why the assistant tool-call message must be saved

When the model asks for a tool, you need to append the assistant message with the tool call data:

```python
message_list.append({
    "role": "assistant",
    "content": assistant_message.content,
    "tool_calls": assistant_message.tool_calls
})
```

This matters because the next message will be a tool result.

The API expects the tool result to correspond to a previous assistant tool call.

This is not enough:

```python
message_list.append({
    "role": "assistant",
    "content": assistant_message.content
})
```

That loses the tool-call metadata.

If you append a tool result without the assistant tool call before it, the API can reject the request.

## Why the model must be called again

Running the tool is not the final step.

After this:

```python
tool_response = TOOL_MAPPING[tool_name](**tool_args)
```

your Python code has the result.

The model does not.

You have to append the result:

```python
message_list.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(tool_response)
})
```

Then call the model again:

```python
response = client.chat.send(
    model="minimax/minimax-m2.7",
    tools=tools,
    messages=message_list
)
```

Only then can the model produce the final answer.

## Running the project

Set your OpenRouter API key:

```bash
export OPENROUTER_API_KEY="your_key_here"
```

Run the app:

```bash
python main.py
```

You should see:

```text
User:
```

Ask it to read a file:

```text
User: what is in example_text.txt
```

To exit:

```text
User: exit
```

or:

```text
User: quit
```

## Adding another tool

To add a new tool, repeat the same pattern:

1. create a new file in `tools/`
2. define a tool schema
3. define the Python function
4. import both in `tools/__init__.py`
5. add the schema to `tools`
6. add the function to `TOOL_MAPPING`

Example: `list_files`.

Create:

```text
tools/list_files.py
```

Add the schema:

```python
list_files_tool = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files in a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "The directory path to inspect."
                }
            },
            "required": ["directory"]
        }
    }
}
```

Add the function:

```python
import os

def list_files(directory):
    return os.listdir(directory)
```

Then register it in `tools/__init__.py`:

```python
from .read_file import read_tool, read_file
from .list_files import list_files_tool, list_files

tools = [
    read_tool,
    list_files_tool
]

TOOL_MAPPING = {
    "read_file": read_file,
    "list_files": list_files
}
```

Now the model can request `list_files`.

## Common mistakes

### The schema name and mapping key do not match

If the schema says:

```python
"name": "read_file"
```

but the mapping says:

```python
TOOL_MAPPING = {
    "read_tool": read_file
}
```

the model may call `"read_file"` and Python will raise a `KeyError`.

The fix:

```python
TOOL_MAPPING = {
    "read_file": read_file
}
```

### The tool result is appended without the assistant tool call

A tool result must come after the assistant message that requested the tool.

Correct order:

```python
message_list.append({
    "role": "assistant",
    "content": assistant_message.content,
    "tool_calls": assistant_message.tool_calls
})

message_list.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(tool_response)
})
```

### The model is not called again after the tool result

This is incomplete:

```python
tool_response = TOOL_MAPPING[tool_name](**tool_args)
message_list.append(...)
print(response.choices[0].message.content)
```

The model still needs another call.

Correct:

```python
tool_response = TOOL_MAPPING[tool_name](**tool_args)
message_list.append(...)

response = client.chat.send(
    model="minimax/minimax-m2.7",
    tools=tools,
    messages=message_list
)
```

### The wrong response variable is updated

If your loop checks:

```python
while response.choices[0].finish_reason == "tool_calls":
```

then update `response` inside the loop.

Do not do this:

```python
response_2 = client.chat.send(...)
```

unless you then assign:

```python
response = response_2
```

Simpler:

```python
response = client.chat.send(...)
```

Otherwise the loop may keep checking the old response forever.

### Too many tools too early

Do not add ten tools at once.

Add one tool, test it, then add the next.

A broken schema or bad mapping is much easier to debug when only one new tool changed.

## Suggested next tools

The next useful tools are:

```text
list_files
write_file
create_folder
search_files
run_shell_command
```

Add them slowly.

The loop does not need to change much. Most of the work is defining clear tool schemas and safe Python functions.

## Safety note

A read-only tool like `read_file` is low risk.

Tools like these are more dangerous:

```text
write_file
delete_file
run_shell_command
edit_file
```

Before adding tools that can change files or run commands, restrict what paths they can touch.

A simple project-root check is a good start:

```python
import os

ALLOWED_ROOT = "/workspaces/Building_an_agent_from_scratch_in_python"

def safe_path(path):
    absolute_path = os.path.abspath(path)

    if not absolute_path.startswith(ALLOWED_ROOT):
        raise ValueError("Access denied: path outside project root")

    return absolute_path
```

Use that inside file tools before reading or writing.

## Where this is going

This project starts with `read_file` because it is the easiest tool to understand.

The same pattern can support more serious tools:

```text
read_file
list_files
write_file
search_files
run_tests
run_shell_command
inspect_git_diff
```

At that point, the project starts to look like a small coding agent.

The primitive loop stays the same:

```text
model asks for tool
Python runs tool
tool result goes back to model
model continues
```

Everything else is just making that loop more useful, safer, and easier to debug.