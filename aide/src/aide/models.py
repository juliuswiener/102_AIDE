import os
import json
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import Tool
from rich import print
from langchain_community.tools.tavily_search import TavilySearchResults
from .tools import (
    read_file_tool,
    write_file_tool,
    command_runner_tool,
    build_code_map_tool,
    load_schema_tool,
    websocket_test_tool,
    run_benchmark_tool,
    request_user_confirmation_tool,
    validate_api_schema_tool,
)

# --- Agent Infrastructure ---

def run_agent_turn(prompt, llm_with_tools, tools_map):
    """Handles a single turn of the agent's ReAct loop."""
    messages = [HumanMessage(content=prompt)]
    while True:
        result = llm_with_tools.invoke(messages)
        messages.append(result)

        if not result.tool_calls:
            final_answer = result.content
            print(f"[bold green]Assistant:[/ ] {final_answer}")
            return final_answer

        print(f"[yellow]Thought:[/ ] {result.content}")

        for tool_call in result.tool_calls:
            if tool_call['name'] == 'request_user_confirmation_tool':
                prompt_text = tool_call['args']['prompt']
                print(f"[bold yellow]Confirmation required:[/bold yellow] {prompt_text} [y/n]")
                user_response = input().lower()
                tool_output = "User confirmed." if user_response == 'y' else "User denied."
                messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))
                continue

            action = f"Action: {tool_call['name']}({tool_call['args']})"
            print(f"[cyan]Action:[/ ] {tool_call['name']}({tool_call['args']})")
            tool_output = tools_map[tool_call["name"]].invoke(tool_call["args"])
            observation = f"Observation: {tool_output}"
            print(f"[magenta]Observation:[/ ] {tool_output}")
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

class Agent:
    """A class to encapsulate agent behavior."""
    def __init__(self, llm_with_tools, tools_map, prompt_path, output_file=None, app_root="."):
        self.llm_with_tools = llm_with_tools
        self.tools_map = tools_map
        self.prompt_path = os.path.join(app_root, prompt_path)
        self.output_file = output_file

    def run(self, **kwargs):
        """Runs the agent for a specific task."""
        try:
            with open(self.prompt_path, "r") as f:
                prompt = f.read().format(**kwargs)
        except Exception as e:
            print(f"[bold red]Error reading prompt file {self.prompt_path}: {e}[/]")
            return None

        result_json = run_agent_turn(prompt, self.llm_with_tools, self.tools_map)

        try:
            result_json = result_json.strip()
            if result_json.startswith("```json"):
                result_json = result_json[7:-4].strip()
            result_data = json.loads(result_json)

            if self.output_file:
                with open(self.output_file, "w") as f:
                    json.dump(result_data, f, indent=4)
                print(f"[bold blue]Output written to {self.output_file}[/]")
            
            # Execute tool calls if present
            if "tool_calls" in result_data and isinstance(result_data["tool_calls"], list):
                for tool_call in result_data["tool_calls"]:
                    tool_name = tool_call.get("tool_name")
                    tool_args = tool_call.get("args", {})
                    if tool_name in self.tools_map:
                        print(f"[cyan]Action:[/ ] {tool_name}({tool_args})")
                        tool_output = self.tools_map[tool_name].invoke(tool_args)
                        print(f"[magenta]Observation:[/ ] {tool_output}")
                    else:
                        print(f"[bold red]Error: Tool '{tool_name}' not found.[/]")

            return result_data
        except (json.JSONDecodeError, AttributeError):
            print(f"[bold red]Error: Agent did not return valid JSON from prompt {self.prompt_path}.[/]")
            if self.output_file:
                report = {
                    "error": f"Invalid JSON response from agent using {self.prompt_path}.",
                    "summary": "Agent failed due to error.",
                    "raw_output": result_json,
                }
                with open(self.output_file, "w") as f:
                    json.dump(report, f, indent=4)
                return report
            return None

# --- LLM and Tool Configurations ---

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

tavily_api_key = os.getenv("TAVILY_API_KEY")


llm_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
llm_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=api_key)

def get_web_search_tool():
    """Returns a tool for performing web searches."""
    if not tavily_api_key:
        print("[bold yellow]Warning: TAVILY_API_KEY not set. Web search will be disabled.[/bold yellow]")
        return None
    return TavilySearchResults(max_results=3)

web_search = get_web_search_tool()
all_tools_list = [
    read_file_tool,
    write_file_tool,
    build_code_map_tool,
    load_schema_tool,
    websocket_test_tool,
    run_benchmark_tool,
    request_user_confirmation_tool,
    validate_api_schema_tool,
    command_runner_tool,
]
if web_search:
    all_tools_list.append(web_search)

all_tools_map = {t.name: t for t in all_tools_list}

implementer_tools = all_tools_list
implementer_tools_map = {t.name: t for t in implementer_tools}
llm_implementer = llm_flash.bind_tools(implementer_tools)
llm_refactor = llm_pro.bind_tools(implementer_tools)

tester_tools = all_tools_list
tester_tools_map = {t.name: t for t in tester_tools}
llm_tester = llm_flash.bind_tools(tester_tools)

default_tools = all_tools_list
llm_default = llm_flash.bind_tools(default_tools)
default_tools_map = {t.name: t for t in default_tools}
