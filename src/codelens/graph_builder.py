import ctypes
from codelens import analyzer
from networkx import generators
import networkx as nx


def build_graph(analysis):
    g=nx.DiGraph()

    for filepath,data in analysis.items():
        file_node=f"file:{filepath}"
        g.add_node(file_node,type="file",name=filepath)

        for func in data["functions"]:
            func_id=f"func:{filepath}:{func['name']}"
            g.add_node(func_id,type="function",name=func["name"],
                       line=func["line"], filepath=filepath)
            g.add_edge(func_id,file_node,type="CONTAINS")
        
        for cls in data["classes"]:
            class_id=f"class:{filepath}:{cls['name']}"
            g.add_node(class_id,type="class",name=cls['name'],filepath=filepath)
            g.add_edge(file_node,class_id,type="CONTAINS")

            for method in cls['methods']:
                method_id=f"func:{filepath}:{cls['name']}.{method['name']}"
                g.add_node(method_id,type="method",name=method['name'],line=method['line'],class_name=cls['name'],filepath=filepath)
                g.add_edge(method_id,class_id,type="contains")

            for base in cls['bases']:
                g.add_edge(class_id, f"__unresolved_class__:{base}", type="INHERITS")
    return g

def resolve_inheritance(g,analysis):
    class_by_name={}
    
    for node,attr in g.nodes(data=True):
        if attr.get('type')=='class':
            class_by_name.setdefault(attr['name'],[]).append(node)
    
    to_add=[]
    to_remove=[]

    for u,v,data in g.edges(data=True):
        if data.get('type')=="INHERITS" and v.startswith('__unresolved_class__'):
            base_name=v.slice(':',1)[1]
            to_remove.append((u,v))

            if base_name in class_by_name:
                for target in class_by_name['base_name']:
                    to_add.append((u,target,{"type" :"INHERITS"}))
    g.remove_edges_from(to_remove)

    for u,v,d in to_add:
        g.add_edge(u,v,**d)

def resolve_calls(g,analysis):
    func_by_name={}

    for node,attr in g.nodes(data=True):
        if attr.get("type")=="function":
            func_by_name.setdefault(attr['name'],[]).append(node)

    for filepath,data in analysis.items():
        import_map={}

        for imp in data["imports"]:
            alias=imp.get("alias") or imp["module"].split(".")[-1]
            import_map[alias]=imp["module"]

        def resolve_one(caller_id,call_name):

            #case 1: self calls
            if call_name.startswith("self."):
                method_name=call_name.split(".",1)[1]
                class_name=g.nodes[caller_id].get('class_name')
                target=f"func:{filepath}{class_name}{method_name}"
                if g.has_node(target):
                    g.add_edge(caller_id,target,type="CALLS")
                    return
            
            #case 2: functions inside module 
            if "." in call_name:
                prefix,func_name=call_name.split(".",1)
                if prefix in import_map:
                    module_name=import_map[prefix].replace(".","/")+".py"
                    target=f"func:{module_name}{func_name}"
                    if g.has_node(target):
                        g.add_edge(caller_id,target,type="CALLS")
                        return

            #case 3: functions within the same file     
            same_file_target=f"func:{filepath}{call_name}"

            if g.has_node(same_file_target):
                g.add_edge(caller_id,same_file_target,type="CALLS")
                return
            
            candidates=func_by_name.get(call_name)
            if candidates and len(candidates)==1:
                g.add_edge(caller_id,candidates[0],type="CALLS")
                return  
            
        for func in data["functions"]:
            caller_id=f"func:{filepath}:{func['name']}"
            for call in func['calls']:
                resolve_one(caller_id,call)

        for cls in data["classes"]:
            for method in cls["methods"]:
                caller_id=f"func:{filepath}:{cls['name']}.{method['name']}"
                for call in method['calls']:
                    resolve_one(caller_id,call)

        
class CodeGraph:

    def __init__(self,analysis):
        self.g=build_graph(analysis)
        resolve_inheritance(self.g,analysis)
        resolve_calls(self.g,analysis)

    def find_node(self,func_name):
        matches=[n for n,a in self.g.nodes(data=True) if a['type']=="function" and (a['name']==func_name or n.endswith(f":{func_name}"))]
        return matches

    def callees(self,func_name):
        """What does the func_name call?"""
        results=[]
        for node in self.find_node(func_name):
            results+=[v for _,v in self.g.out_edges(node) if self.g.edges[node,v]["type"]=="CALLS"]

        return results

    def callers(self,func_name):
        """What calls func_name?"""
        results=[]
        for node in self.find_node(func_name):
            results+=[u for u,_ in self.g.in_edges(node) if self.g.edges[u,node]["type"]=="CALLS"]

        return results
    
    def call_chain(self,func_name,max_depth=5):
        import collections
        start_list=self.find_node(func_name)
        visited=set(start_list)
        queue=collections.deque([(n,0) for n in start_list])
        chain=[]

        while queue:
            node,depth=queue.popleft()

            if depth>=max_depth:
                continue
            for _,v in self.g.out_edges(node):
                if self.g.edges[node,v]["type"]=="CALLS" and v not in visited:
                    visited.add(v)
                    chain.append((depth+1,v))
                    queue.append((v,depth+1))

        return chain

    
