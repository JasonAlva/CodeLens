
import os
import argparse

from fastmcp import FastMCP

from . import tools
from .analyzer import analyze_repo
from .graph_builder import CodeGraph
from .vector_search import build_search_index


mcp=FastMCP(name="codelens-mcp")

_repo_path=None
_cache={}

def _graph():
    if "graph" not in _cache:
        analysis=analyze_repo(_repo_path)
        _cache['analysis']=analysis
        _cache['graph']=CodeGraph(analysis)
    return _cache['graph']

def _index():
    if "index" not in _cache:
        _graph()
        _cache['index'],_cache['chunks']=build_search_index(_cache['analysis'],_repo_path)
    return _cache['index'],_cache['chunks']

@mcp.tool()
def search_code(query:str)->str:
    """Semantic search over the codebase. Use for 'what/where' questions in
    natural language (e.g. 'where is password verification done')."""
    index,chunks=_index()
    return tools.search_code(query,index,chunks,_graph())

@mcp.tool()
def get_callers(fn:str)->str:
    """List every function that calls the given function (exact name).
    Use to see who depends on a piece of code."""
    return tools.get_callers(_graph(),fn)

@mcp.tool()
def get_callees(fn:str)->str:
    """List every function that is called by the given function (exact name).
    Use to see what function depends on"""
    return tools.get_callees(_graph(),fn)

@mcp.tool()
def impact_analysis(target: str) -> str:
    """Change-impact report for a function or class: what breaks if it is
    modified, ranked by severity, plus likely tests to run."""
    return tools.impact_analysis(_graph(), _repo_path, target)

def main():
    global _repo_path
    parser=argparse.ArgumentParser(prog="codelens-mcp")
    parser.add_argument("--repo",required=True,help="path of the repo to be analyzed")
    args=parser.parse_args()
    _repo_path=os.path.abspath(args.repo)
    mcp.run(transport='stdio')


if __name__=="__main__":
    main()