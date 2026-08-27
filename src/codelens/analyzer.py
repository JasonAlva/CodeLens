import datetime
import typing_extensions
import functools
import pathlib
import os
import ast
import json

SKIP_DIRS = {".venv","env",".env","build","dist",".git","__pycache__","node_modules","venv","venv3",".venv3"}

def collect_files(repo_path:str):
    py_files=[]
    for root,dirs,files in os.walk(repo_path):
        dirs[:]=[d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root,f))

    return py_files

def parse_files(filename):
    with open(filename,"r",encoding="utf-8") as f: 
        source=f.read()
    return ast.parse(source,filename)


class CodeVisitor(ast.NodeVisitor):
    
    def __init__(self):
        self.classes=[]
        self.functions=[]
        self.imports=[]
        self._current_class=None

    def visit_ClassDef(self,node):
        bases=[ast.unparse(b) for b in node.bases]
        cls={
            "name":node.name,
            "bases":bases,
            "line":node.lineno,
            "methods":[]
            
        }
        self.classes.append(cls)
        prev_class=self._current_class
        self._current_class=cls
        self.generic_visit(node)
        self._current_class=prev_class

    def visit_FunctionDef(self,node):
        calls=self._extract_calls(node)
        func={
            "name":node.name,
            "line":node.lineno,
            "calls":calls,
            "docs":ast.get_docstring(node),                          
            "decorators":[ast.unparse(d) for d in node.decorator_list]  
                    
        }

        if self._current_class:
            self._current_class["methods"].append(func)
        else:
            self.functions.append(func)

        self.generic_visit(node)

    # handle async functions the same way
    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self,node): 
        for alias in node.names:
            self.imports.append({"module":alias.name,"alias":alias.asname})

    def visit_ImportFrom(self,node):
        for alias in node.names:
            self.imports.append({
                "module":f"{node.module}.{alias.name}" if node.module else alias.name, 
            })

    def _extract_calls(self,func_node):
        calls=[]
        for node in ast.walk(func_node):
            if isinstance(node,ast.Call):
                calls.append(self._call_name(node.func))
            
        return [c for c in calls if c]

    def _call_name(self,node):
        if isinstance(node,ast.Name):
            return node.id
        if isinstance(node,ast.Attribute):
            base=self._call_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return None


def analyze_repo(repo_path):
    results={}
    
    for filepath in collect_files(repo_path):
        try:
            tree=parse_files(filepath)
        except SyntaxError as e:
            print(f"skipping file {filepath}: {e}")
            continue

        visitor=CodeVisitor()
        visitor.visit(tree)

        relpath=os.path.relpath(filepath,repo_path)

        results[relpath]={
            "classes":visitor.classes,
            "functions":visitor.functions,
            "imports":visitor.imports
        }

    return results

def save_json(data,out_path="output.json"):
    with open(out_path,"w",encoding="utf-8") as f:  
        json.dump(data,f,indent=2)