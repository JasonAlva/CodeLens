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
    args=parser.parse_args()
    print(f"analyzing {args.repo}")
    result=analyze_repo(args.repo)
    graph=CodeGraph(result)
    print("callers of save_user():", graph.callers("save_user"))
    print("callees of save_user():", graph.callees("save_user"))
    save_json(result,args.out)
    print("output.json is created")
    if args.impact:
        print(impact_report(graph,args.impact,args.repo))
        return



if __name__== "__main__":
    main()
    
    