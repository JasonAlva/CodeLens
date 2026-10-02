
from codelens.vector_search import search
from codelens.vector_search import build_search_index
import argparse
from .analyzer import analyze_repo,save_json
from .graph_builder import CodeGraph
from .impact import impact_report



def main():
    parser=argparse.ArgumentParser(
        prog="codelens"
    )
    parser.add_argument("--repo",required=True,help="Repository path")
    parser.add_argument("--out",default="output.json",help="output file")
    parser.add_argument("--impact",help="function to generate the impact report")
    parser.add_argument("--search",help="user query")
    args=parser.parse_args()
    print(f"analyzing {args.repo}")
    result=analyze_repo(args.repo)
    graph=CodeGraph(result)
    save_json(result,args.out)
    print("output.json is created")
    index,chunks=build_search_index(result,args.repo)
    if args.impact:
        print(impact_report(graph,args.impact,args.repo))
        return
    if args.search:
        hits=search(args.search,index,chunks,graph)
        print(hits)
        return


if __name__== "__main__":
    main()
    
    