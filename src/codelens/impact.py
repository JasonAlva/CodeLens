from networkx.algorithms import simple_paths
from numpy import append
import collections
from .graph_builder import CodeGraph
import os

def find_impacted_by_node(graph:CodeGraph,start_nodes,max_depth=10):
    visited=set(start_nodes)
    queue=collections.deque([(n,0) for n in start_nodes])
    impact=[]

    while queue:
        node,depth=queue.popleft()

        if(depth>=max_depth):
            continue
        for u,v in graph.g.in_edges(node):
            if graph.g.edges[u,node]["type"]=="CALLS" and u not in visited:
                visited.add(u)
                impact.append((depth+1,u))
                queue.append((u,depth+1))           
    return impact

def find_impacted(graph:CodeGraph,target,max_depth=10):
    impacted={}
    for start in graph.find_node(target):
        for depth,node in find_impacted_by_node(graph,[start],max_depth):
            impacted[node]=min(depth,impacted.get(node,999))

    return sorted(impacted.items(),key=lambda x:x[1])

def find_impacted_class(graph:CodeGraph,class_name,max_depth=10):

    method_nodes=[n for n,a in graph.g.nodes(data=True) if a.get("type")=="function" and a.get("class_name")==class_name]

    class_nodes=[n for n,a in graph.g.nodes(data=True) if a.get("type")=="class" and a["name"]==class_name]

    subclasses=[]

    for cls in class_nodes:
        for u,v in graph.g.in_edges(cls):
            if graph.g.edges[u,v]["type"]=="INHERITS":
                subclasses.append(u) 
    
    all_impacted={}

    for m in method_nodes:
        for depth,node in find_impacted(graph,m,max_depth):
            all_impacted[node]=min(depth,all_impacted.get(node,999))

    for sc in subclasses:
        all_impacted[sc]=min(1,all_impacted.get(sc,999))    

    return sorted(all_impacted.items(),key=lambda x: x[1])

def bucket_by_severity(impacted):
    high=[n for n,d in impacted if d==1]
    medium=[n for n,d in impacted if d in (2,3)]
    low=[n for n,d in impacted if d>3]
    
    return {"high":high,"medium":medium,"low":low}
    
def find_likely_tests(impacted_files,repo_path):
    test_map={}
    for filepath in impacted_files:
        basename=os.path.basename(filepath)
        stem_name=basename.replace(".py","")
        candidates=[f"test_{stem_name}.py",f"{stem_name}_test.py",os.path.join("tests",f"test_{stem_name}.py")]
        found=[c for c in candidates if os.path.exists(os.path.join(repo_path,c))]
        test_map[filepath]=found
    return test_map

def impact_report(graph:CodeGraph,target_name,repo_path,max_depth=10):
    impacted=find_impacted(graph,target_name,max_depth)
    buckets=bucket_by_severity(impacted)

    affected_files=sorted({graph.g.nodes[n].get("filepath")for n,_ in impacted if graph.g.nodes[n].get("filepath")})

    test_files=find_likely_tests(affected_files,repo_path)

    lines=[]
    severity="HIGH IMPACT" if buckets['high'] else ( "MEDIUM IMPACT" if buckets['medium']else "LOW IMPACT")
    lines.append(f"{severity}/{len(affected_files)} function depends on {target_name}")
    lines.append(f"Affected files : {', '.join(affected_files) if affected_files else 'none'}")


    all_tests=sorted({ t for ts in test_files.values() for t in ts})
    lines.append(f"test files to run: {', '.join(all_tests) if all_tests else 'none test files found'}")

    lines.append("")
    for n in buckets["high"]:
        lines.append(f" -  {graph.g.nodes[n].get('name',n)}({graph.g.nodes[n].get('filepath','?')})")

    return "\n".join(lines)