import argparse
from .analyzer import analyze_repo,save_json
from .graph_builder import CodeGraph



def main():
    parser=argparse.ArgumentParser(
        prog="codelens"
    )
    parser.add_argument("--repo",required=True,help="Repository path")
    parser.add_argument("--out",default="output.json",help="output file")
    args=parser.parse_args()
    print(f"analyzing {args.repo}")
    result=analyze_repo(args.repo)
    graph=CodeGraph(result)
    print("callers of login():", graph.callers("save_user"))
    print("callees of login():", graph.callees("save_user"))
    save_json(result,args.out)
    print("output.json is created")
    


if __name__== "__main__":
    main()
    
    