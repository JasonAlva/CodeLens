
from codelens import graph_builder
from codelens import graph_builder
from codelens import graph_builder
from codelens import graph_builder
from operator import index
from codelens.graph_builder import CodeGraph
from sentence_transformers import SentenceTransformer
import os
import numpy as np

def chunk_repo(analysis,repo_path):
    chunks=[]
    
    for filepath,data in analysis.items():
        filename=os.path.join(repo_path,filepath)
        with open(filename,mode="r") as f:
            lines=f.readlines()
        
        def extractSource(func):
            start=func['line']-1
            end=func['end_line']
            return "".join(lines[start:end])

        for func in data["functions"]:
            chunks.append({
                "id":f"func:{filepath}:{func['name']}",
                "filepath":filepath,
                "name":func['name'],
                "code":extractSource(func),
                "docstring":func.get('docstring')       
            })

        for cls in data["classes"]:
            for method in cls["methods"]:
                chunks.append({
                "id":f"func:{filepath}:{cls['name']}.{method['name']}",
                "filepath":filepath,
                "name":method['name'],
                "code":extractSource(method),
                "docstring":method.get('docstring')         
            })

    return chunks

_model=None

def get_model():
    global _model
    if _model is None:
        _model=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return _model

def embed_chunks(chunks):
    model=get_model()
    text=[f"{ch['name']}\n{ch['docstring'] or ''}\n{ch['code']}"for ch in chunks]
    vectors=model.encode(text,show_progress_bar=True)
    for chunk,vec in zip(chunks,vectors):
        chunk["embedding"]=vec
    return chunks

def build_vector_index(chunks):
    matrix=np.array([c['embedding'] for c in chunks])
    norms=np.linalg.norm(matrix,axis=1,keepdims=True)
    normalized=matrix/norms
    return normalized,chunks

def semantic_search(query,index,chunks,top_k=5):
    model=get_model()
    q_vector=model.encode(query)
    q_vector=q_vector/np.linalg.norm(q_vector)

    scores=index@q_vector
    top_indices=np.argsort(scores)[::-1][:top_k]

    return [{"chunk":chunks[i], "score":scores[i] } for i in top_indices]

def graph_rag_search(query,index,chunks,graph:CodeGraph,top_k=3):
    hits=semantic_search(query,index,chunks,top_k)
    enriched=[]
    for hit in hits:
        node=hit['chunk']['id']
        callers=list(graph.g.predecessors(node) if graph.g.has_node(node) else []) 
        callees=list(graph.g.successors(node) if graph.g.has_node(node) else []) 
        enriched.append({
            **hit,
            "callers":callers,
            "callees":callees
        })

    return enriched

def build_search_index(analysis,repo_path):
    chunks=chunk_repo(analysis,repo_path)
    embedded_chunks=embed_chunks(chunks)
    index,chunks=build_vector_index(embedded_chunks)
    return index, chunks

def search(query,index,chunks,graph:CodeGraph):
    return graph_rag_search(query,index,chunks,graph)
     
