from openrouter import OpenRouter
import os

from read_file import TOOL_MAPPING

message_list = []

def chat(messages, tools:list = []):
    with OpenRouter(
        api_key=os.getenv("OPENROUTER_API_KEY")
    ) as client:
        
        response = client.chat.completions.create(
            model="gpt-4o",
            tools=tools,
            messages=messages
        )

        if response.choices[0].finish_reason == "tool_calls":
            message_list.append({"role": "assistant", "content": response.choices[0].message.content})
            tool_calls = response.choices[0].tool_calls
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tool_response = TOOL_MAPPING[tool_name](**tool_args)
                message_list.append(
                    {"role": "tool",
                     "tool_call_id": tool_call.id,
                     "content": json.dumps(tool_response)
                    }
                )


    return  response.choices[0].message.content



