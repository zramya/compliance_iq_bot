import re
import psycopg
import os
from app.core.db import get_vector_store
from psycopg.rows import dict_row
from langchain_core.tools import tool

# PGVector connection string uses SQLAlchemy format: postgresql+psycopg://...
# psycopg.connect needs standard format: postgresql://...
_raw_conn = os.getenv("PG_CONNECTION_STRING_FTS")


@tool
def vector_search_tool(
    query: str,
    k: int = 5,
    collection_name: str = "reg_compliance_iq_bot",
):
    """
    Semantic Vector Search.

    Use for:

    - Definitions
    - Concepts
    - Explanations
    - Regulatory guidance
    - Policies
    - General compliance questions

    Examples:

    - What is CET1?
    - Explain ICAAP.
    - What is CRR?

    Do NOT use for:

    - Circular IDs
    - Regulation numbers
    - Section numbers
    - Clause numbers
    - Notification IDs
    """
    print("=" * 80)
    print("VECTOR SEARCH")
    print("Query:", query)
    print("=" * 80)
    return _search_vector(
        query=query,
        k=k,
        collection_name=collection_name,
    )


@tool
def hybrid_search_tool(
    query: str,
    k: int = 5,
    collection_name: str = "reg_compliance_iq_bot",
):
    """
    Hybrid Search (FTS + Vector).

    Use ONLY when:

    1. The query contains an exact regulatory reference
    AND
    2. The user asks for its explanation.

    Examples:

    - Explain RBI/2025-26/27
    - Explain Section 13(2)
    - Explain Regulation 23

    Do not use for:

    - Pure definitions
    - Pure identifier lookups
    """
    print("=" * 80)
    print("HYBRID SEARCH")
    print("Query:", query)
    print("=" * 80)
    return _search_hybrid(
        query=query,
        k=k,
        collection_name=collection_name,
    )


@tool
def metadata_search_tool(
    query: str,
    regulation_type: str | None = None,
    k: int = 5,
    collection_name: str = "reg_compliance_iq_bot",
):
    """
    PostgreSQL Full Text Search (FTS).

    Best for:
    - RBI Circular IDs
    - Regulation numbers
    - Section numbers
    - Clause numbers
    - Notification IDs
    - Exact regulatory keywords

    Use only for exact lookups.
    Do not use for conceptual explanations.
    """

    print("=" * 80)
    print("Running Metadata (FTS) Search")
    print("Query:", query)
    print("Regulation Type:", regulation_type)
    print("=" * 80)

    if regulation_type:
        sql = """
        SELECT
            e.document AS content,
            e.cmetadata AS metadata,
            ts_rank(
                to_tsvector('english', e.document),
                plainto_tsquery('english', %(query)s)
            ) AS score

        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c
            ON c.uuid = e.collection_id

        WHERE
            c.name = %(collection)s
            AND e.cmetadata->>'regulation_type' = %(regulation_type)s
            AND (
                e.document ILIKE %(like_query)s
                OR to_tsvector('english', e.document)
                   @@ plainto_tsquery('english', %(query)s)
            )

        ORDER BY
            CAST(COALESCE(e.cmetadata->>'version', '0') AS FLOAT) DESC,
            score DESC

        LIMIT %(k)s;
        """

        params = {
            "query": query,
            "like_query": f"%{query}%",
            "collection": collection_name,
            "regulation_type": regulation_type,
            "k": k,
        }

    else:
        sql = """
        SELECT
            e.document AS content,
            e.cmetadata AS metadata,
            ts_rank(
                to_tsvector('english', e.document),
                plainto_tsquery('english', %(query)s)
            ) AS score

        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c
            ON c.uuid = e.collection_id

        WHERE
            c.name = %(collection)s
            AND (
                e.document ILIKE %(like_query)s
                OR to_tsvector('english', e.document)
                   @@ plainto_tsquery('english', %(query)s)
            )

        ORDER BY
            score DESC

        LIMIT %(k)s;
        """

        params = {
            "query": query,
            "like_query": f"%{query}%",
            "collection": collection_name,
            "k": k,
        }

    with psycopg.connect(_raw_conn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    output = [
        {
            "content": row["content"],
            "metadata": row["metadata"],
            "score": float(row["score"]),
        }
        for row in rows
    ]

    print(f"Returned {len(output)} results")
    return output


def _search_fts(query: str, k: int, collection_name: str):
    """Keyword search against the stored chunks using Postgres' tsvector/tsquery/ts_rank"""
    sql = """
       SELECT
           e.document                                               AS content,
           e.cmetadata                                              AS metadata,
           ts_rank(
               to_tsvector('english', e.document),
               plainto_tsquery('english', %(query)s)
           )                                                        AS fts_rank
       FROM  langchain_pg_embedding  e
       JOIN  langchain_pg_collection c ON c.uuid = e.collection_id
       WHERE c.name = %(collection)s
         AND to_tsvector('english', e.document)
             @@ plainto_tsquery('english', %(query)s)
       ORDER BY fts_rank DESC
       LIMIT %(k)s;
   """
    print("Running FTS Search")
    with psycopg.connect(_raw_conn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"query": query, "collection": collection_name, "k": k})
            rows = cur.fetchall()

    output = [
        {
            "content": row["content"],
            "metadata": row["metadata"],
            "fts_rank": round(float(row["fts_rank"]), 4),
        }
        for row in rows
    ]

    print(output)
    return output


def _search_vector(query: str, k: int, collection_name: str):
    vector_store = get_vector_store(collection_name)
    docs = vector_store.similarity_search(query, k)

    output = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in docs
    ]
    print("Running Vector Search")
    print(output)
    return output


def _search_hybrid(query: str, k: int, collection_name: str):
    """Merge vector and fts results using RRF (Reciprocal Rank Fusion)
    Chunks appearing in both search results will rank higher than those in only one
    The constant 60 prevents top-ranked outputs from dominating
    How RRF scores for a chunk = sum of 1/(rank + 60)
    """
    print("Running Hybrid Search")

    vector_search_results = _search_vector(query, 5, collection_name)
    fts_results = _search_fts(query, 5, collection_name)

    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}
    for rank, doc in enumerate(vector_search_results):
        key = doc["content"][:120]
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (60 + rank + 1)
        chunk_map[key] = {"content": doc["content"], "metadata": doc["metadata"]}
    for rank, item in enumerate(fts_results):
        key = item["content"][:120]
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (60 + rank + 1)
        chunk_map[key] = {"content": item["content"], "metadata": item["metadata"]}
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    print(ranked)
    return [chunk_map[key] for key, _ in ranked[:k]]
