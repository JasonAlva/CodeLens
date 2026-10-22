from codelens.graph_builder import CodeGraph
from .impact import impact_report
from .vector_search import graph_rag_search


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

def impact_analysis(graph:CodeGraph,target_name:str,repo_path:str):
    return impact_report(graph,target_name,repo_path)

def get_callers(graph:CodeGraph,function_name):
    neighbors=list(graph.callers(function_name))
    return ', '.join(neighbors) if neighbors else f"no callers found for {function_name}"

def get_callees(graph:CodeGraph,function_name):
    neighbors=list(graph.callees(function_name))
    return ', '.join(neighbors) if neighbors else f"no callees found for {function_name}"


