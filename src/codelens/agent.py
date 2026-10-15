from huggingface_hub.errors import GatedRepoError
from torch import mode
from google import genai
from google.genai import types
from .impact import impact_report
from .vector_search import graph_rag_search

client=genai.Client()

MODEL = "gemini-3.5-flash-lite"  

SYSTEM_PROMPT = """You are CodeLens, an assistant that answers questions about a codebase
using graph and semantic search tools. Always use tools to look up real information
rather than guessing. Chain multiple tool calls when a question requires it
(e.g. tracing a flow across several functions)."""

TOOLS = [
    {
        "type": "function",
        "name": "search_code",
        "description": "Semantic search over the codebase. Use for 'what/where' questions described in natural language (e.g. 'where is auth handled').",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language description of what to find"}
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "get_callers",
        "description": "Find every function that calls a given function. Use to trace who depends on a piece of code.",
        "parameters": {
            "type": "object",
            "properties": {"fn": {"type": "string", "description": "Exact function name"}},
            "required": ["fn"],
        },
    },
    {
        "type": "function",
        "name": "get_callees",
        "description": "Find every function called by a given function. Use to trace what a function depends on.",
        "parameters": {
            "type": "object",
            "properties": {"fn": {"type": "string", "description": "Exact function name"}},
            "required": ["fn"],
        },
    },
    {
        "type": "function",
        "name": "impact_analysis",
        "description": "Change-impact report for a function or class: what breaks if it is modified, ranked by severity, plus likely tests. Use for 'what if I change X' questions.",
        "parameters": {
            "type": "object",
            "properties": {"target": {"type": "string", "description": "Function or class name"}},
            "required": ["target"],
        },
    },
]


def search_code(query,index,chunks,graph):
    results=graph_rag_search(query,index,chunks,graph,top_k=5)
    if not results:
        return "no relevant answer found"
    lines=[]
   

    for r in results:
        chunk=r['chunk']
        score=r['score']
        lines.append(f"- {chunk['name'] , chunk['filepath']}, score={score:.2f}")
        if r['callers']:
            lines.append(f"called by :{','.join(r['callers'])} ")
        if r['callees']:
            lines.append(f"calls :{','.join(r['callees'])} ")
    
    return "/n".join(lines)

def impact_analysis(graph,target_name:str,repo_path:str):
    return impact_report(graph,target_name,repo_path)



def ask(question,graph,index,chunks,repo_path,max_turns=4):

    interaction=client.interactions.create(model=MODEL,
    input=question,
    system_instruction=SYSTEM_PROMPT,
    tools=TOOLS)

    for _ in range(max_turns):

        calls=[s for s in interaction.steps if s.type=="function_call"]

        if not calls:
            return interaction.output_text

        result=[]

        for call in calls:
            print(f"{call.name, (dict(call.arguments))}")
            try:
                output=dispatch_tool(call.name,dict(call.arguments),graph,index,chunks,repo_path)
            except Exception as e:
                output=f"error:{e}"
            
            result.append({
                "type":"function_result",
                "name":call.name,
                "call_id":call.id,
                "result":[{"type":"text","text":str(output)}]
            })
        
       
        interaction=client.interactions.create(model=MODEL,
                input=result,
                system_instruction=SYSTEM_PROMPT,
                tools=TOOLS,
                previous_interaction_id=interaction.id)

    return "max turns consumed already"



def dispatch_tool(name,args,graph,index,chunks,repo_path):
    if name=='search_code':
        return search_code(args['query'],index,chunks,graph)
    elif name=='get_callers':
        neighbors=list(graph.predecessors(args['fn']))
        return ', '.join(neighbors) if neighbors else f"no callers found for {args['fn']}"
    elif name=='get_callees':
        neighbors=list(graph.successors(args['fn']))
        return ', '.join(neighbors) if neighbors else f"no callees found for {args['fn']}"
    elif name=='impact_analysis':
        return impact_analysis(graph,args['target'],repo_path)
    else :
        return f"unknown tool: {name}"
