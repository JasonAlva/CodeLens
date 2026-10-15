from torch import return_types
from dotenv import load_dotenv
load_dotenv()

from codelens.vector_search import search
from codelens.vector_search import build_search_index
import argparse
from .analyzer import analyze_repo,save_json
from .graph_builder import CodeGraph
from .impact import impact_report
from .agent import ask



def main():
    parser=argparse.ArgumentParser(
        prog="codelens"
    )
    parser.add_argument("--repo",required=True,help="Repository path")
    parser.add_argument("--out",default="output.json",help="output file")
    parser.add_argument("--impact",help="function to generate the impact report")
    parser.add_argument("--search",help="user query")
    parser.add_argument("--ask",help="ask agent a question")
    args=parser.parse_args()

    print(f"analyzing {args.repo}")

    result=analyze_repo(args.repo)
    graph=CodeGraph(result)

    save_json(result,args.out)
    print("output.json is created")

    
    if args.impact:
        print(impact_report(graph,args.impact,args.repo))
        return

    if args.search or args.ask:
        index,chunks=build_search_index(result,args.repo)
        if args.search:
            for hit in search(args.search,index,chunks,graph):
                print(f"{hit['score']:.2f}  {hit['chunk']['name']}  ({hit['chunk']['filepath']})")
                return
        
        if args.ask:
            print(ask(args.ask,graph,index,chunks,args.repo))
            return

if __name__== "__main__":
    main()
    
    