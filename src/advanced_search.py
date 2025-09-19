import os
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import whoosh.index as index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import QueryParser
from whoosh import scoring
import json

class AdvancedSearch:
    def __init__(self, index_dir: str = 'search_index'):
        self.index_dir = index_dir
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model
        self.schema = Schema(
            doc_id=ID(stored=True, unique=True),
            filename=TEXT(stored=True),
            content=TEXT,
            metadata=STORED,
            embedding=STORED
        )
        self._create_index_if_needed()

    def _create_index_if_needed(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            ix = index.create_in(self.index_dir, self.schema)

    def index_document(self, doc_id: str, filename: str, content: str, metadata: Dict[str, Any]):
        """Index a document for search"""
        embedding = self.model.encode(content).tolist()

        ix = index.open_dir(self.index_dir)
        writer = ix.writer()
        writer.add_document(
            doc_id=doc_id,
            filename=filename,
            content=content,
            metadata=json.dumps(metadata),
            embedding=json.dumps(embedding)
        )
        writer.commit()

    def full_text_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform full-text search using Whoosh"""
        ix = index.open_dir(self.index_dir)
        with ix.searcher(weighting=scoring.BM25F) as searcher:
            query_parser = QueryParser("content", ix.schema)
            parsed_query = query_parser.parse(query)
            results = searcher.search(parsed_query, limit=limit)

            search_results = []
            for hit in results:
                search_results.append({
                    'doc_id': hit['doc_id'],
                    'filename': hit['filename'],
                    'score': hit.score,
                    'metadata': json.loads(hit['metadata'])
                })
            return search_results

    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        query_embedding = self.model.encode(query)

        ix = index.open_dir(self.index_dir)
        with ix.searcher() as searcher:
            results = []
            for doc in searcher.all_stored_fields():
                doc_embedding = np.array(json.loads(doc['embedding']))
                similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
                results.append({
                    'doc_id': doc['doc_id'],
                    'filename': doc['filename'],
                    'similarity': float(similarity),
                    'metadata': json.loads(doc['metadata'])
                })

            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Combine full-text and semantic search"""
        fts_results = self.full_text_search(query, limit=limit*2)
        semantic_results = self.semantic_search(query, limit=limit*2)

        # Combine and deduplicate
        combined = {}
        for result in fts_results + semantic_results:
            doc_id = result['doc_id']
            if doc_id not in combined:
                combined[doc_id] = result
            else:
                # Average scores
                if 'score' in result and 'score' in combined[doc_id]:
                    combined[doc_id]['score'] = (combined[doc_id]['score'] + result['score']) / 2
                elif 'similarity' in result:
                    combined[doc_id]['similarity'] = result['similarity']

        # Sort by combined score
        sorted_results = list(combined.values())
        sorted_results.sort(key=lambda x: x.get('score', 0) + x.get('similarity', 0), reverse=True)
        return sorted_results[:limit]

    def filter_by_metadata(self, filters: Dict[str, Any], results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter search results by metadata"""
        filtered = []
        for result in results:
            match = True
            for key, value in filters.items():
                if key not in result['metadata'] or result['metadata'][key] != value:
                    match = False
                    break
            if match:
                filtered.append(result)
        return filtered