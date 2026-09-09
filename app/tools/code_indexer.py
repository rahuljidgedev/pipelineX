import os
import re
from pathlib import Path
from rank_bm25 import BM25Okapi

class KotlinCodeIndexer:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.files_data = []
        self.corpus = []
        self.bm25 = None
        self._index_workspace()
        
    def _extract_tokens(self, text: str) -> list[str]:
        # Simple extraction: words and CamelCase splitting
        # Remove comments
        text = re.sub(r'//.*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        # Extract potential identifiers
        identifiers = re.findall(r'[a-zA-Z_]\w*', text)
        
        # Split camel case
        tokens = []
        for ident in identifiers:
            split = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', ident)).split()
            tokens.extend([t.lower() for t in split])
        
        return tokens

    def _index_workspace(self):
        for root, _, files in os.walk(self.workspace_path):
            if "build" in root or ".gradle" in root:
                continue
            for file in files:
                if file.endswith(".kt") or file.endswith(".kts") or file.endswith(".xml"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    rel_path = os.path.relpath(file_path, self.workspace_path)
                    
                    tokens = self._extract_tokens(content)
                    
                    self.files_data.append({
                        "path": rel_path,
                        "content": content
                    })
                    self.corpus.append(tokens)
                    
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.bm25:
            return []
            
        query_tokens = self._extract_tokens(query)
        if not query_tokens:
            return []
            
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top K
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "path": self.files_data[idx]["path"],
                    "content": self.files_data[idx]["content"],
                    "score": scores[idx]
                })
                
        return results
