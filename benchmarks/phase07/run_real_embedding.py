"""Run genuine local CPU inference on pinned external model weights.

No API-based embeddings, mocks, Qdrant publication or organization data.
This executable is intended for disposable GitHub CI Group B and emits a
machine-readable artifact only after model weights and inference succeed.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
import psutil

from benchmarks.phase07.metrics import evaluate, load_dataset

MODELS = {
    "e5-small": {
        "id": "intfloat/multilingual-e5-small",
        "revision": "614241f",
        "license": "mit",
        "dimension": 384,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    "minilm-l12": {
        "id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "revision": "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
        "license": "apache-2.0",
        "dimension": 384,
        "query_prefix": "",
        "passage_prefix": "",
    },
}


def percentiles_ms(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("no_timing_samples")
    return {
        "p50": round(float(np.percentile(values, 50)), 3),
        "p95": round(float(np.percentile(values, 95)), 3),
        "p99": round(float(np.percentile(values, 99)), 3),
    }


def encode(model, texts: list[str], *, prefix: str, batch_size: int) -> np.ndarray:
    values = np.asarray(
        model.encode(
            [prefix + text for text in texts],
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ),
        dtype=np.float32,
    )
    if (
        values.shape != (len(texts), 384)
        or not np.all(np.isfinite(values))
        or not np.all(np.linalg.norm(values, axis=1) > 0)
    ):
        raise ValueError("invalid_real_model_embedding_output")
    return values


def run(model_slug: str, dataset_path: Path) -> dict:
    from huggingface_hub import HfApi, hf_hub_download
    from sentence_transformers import SentenceTransformer
    import sentence_transformers
    import torch
    import transformers

    config = MODELS[model_slug]
    dataset, checksum = load_dataset(dataset_path)
    # Public Hub model metadata is checked *before* any model code is executed.
    info = HfApi().model_info(config["id"], revision=config["revision"])
    if info.gated or not info.sha.startswith(config["revision"]):
        raise ValueError("unexpected_or_gated_model_revision")
    tags = set(info.tags or [])
    card = info.card_data
    license_id = getattr(card, "license", None) or next(
        (tag.removeprefix("license:") for tag in tags if tag.startswith("license:")), None
    )
    if license_id != config["license"]:
        raise ValueError("model_license_not_verified")
    if not any(s.rfilename == "model.safetensors" for s in (info.siblings or [])):
        raise ValueError("safetensors_weight_file_missing")
    # Pin the snapshot to its *resolved full immutable SHA*, not a moving main.
    revision = info.sha
    started = time.perf_counter()
    torch.set_num_threads(2)
    model = SentenceTransformer(
        config["id"],
        revision=revision,
        device="cpu",
        trust_remote_code=False,
        model_kwargs={"use_safetensors": True},
    )
    model.max_seq_length = min(model.max_seq_length, 128)
    model.eval()
    model_load_s = round(time.perf_counter() - started, 3)
    if model.get_sentence_embedding_dimension() != config["dimension"]:
        raise ValueError("actual_embedding_dimension_mismatch")
    process = psutil.Process()
    rss_loaded_mb = round(process.memory_info().rss / 1048576, 2)
    weights_path = hf_hub_download(config["id"], "model.safetensors", revision=revision)
    digest = hashlib.file_digest(open(weights_path, "rb"), "sha256").hexdigest()
    documents = dataset["documents"]
    queries = dataset["queries"]
    # Warm model in the same process, never per-request loading.
    _ = encode(model, [documents[0]["text"]], prefix=config["passage_prefix"], batch_size=1)
    _ = encode(model, [queries[0]["text"]], prefix=config["query_prefix"], batch_size=1)

    start = time.perf_counter()
    doc_embeddings = encode(
        model, [d["text"] for d in documents], prefix=config["passage_prefix"], batch_size=4
    )
    doc_encode_ms = round((time.perf_counter() - start) * 1000, 3)
    query_embeddings = []
    query_ms: list[float] = []
    for query in queries:
        started = time.perf_counter()
        vector = encode(model, [query["text"]], prefix=config["query_prefix"], batch_size=1)
        query_ms.append((time.perf_counter() - started) * 1000)
        query_embeddings.append(vector[0])
    qvec = np.stack(query_embeddings)
    rankings: dict[str, list[str]] = {}
    search_ms: list[float] = []
    for i, query in enumerate(queries):
        started = time.perf_counter()
        allowed = [
            index
            for index, doc in enumerate(documents)
            if doc["domain"] == query["domain"] and doc["scope"] == query["authorized_scope"]
        ]
        # Cosine is dot product because encode() L2-normalized every real vector.
        scores = np.matmul(doc_embeddings[allowed], qvec[i])
        order = sorted(
            range(len(allowed)),
            key=lambda j: (-float(scores[j]), documents[allowed[j]]["id"]),
        )
        rankings[query["id"]] = [documents[allowed[j]]["id"] for j in order]
        search_ms.append((time.perf_counter() - started) * 1000)

    results = evaluate(dataset, rankings)
    weights_mb = round(os.path.getsize(weights_path) / 1048576, 2)
    report = {
        "status": "EXECUTED_REAL_CPU_INFERENCE",
        "candidate": model_slug,
        "model_id": config["id"],
        "revision_full": revision,
        "license_declared_by_hub": license_id,
        "license_legal_approval": "NOT_SIGNED",
        "weights_sha256": digest,
        "weights_file_mb": weights_mb,
        "embedding_dimension_measured": int(doc_embeddings.shape[1]),
        "distance": "Cosine",
        "model_max_sequence_length_used": model.max_seq_length,
        "prefix_policy": {
            "query": config["query_prefix"], "passage": config["passage_prefix"]
        },
        "dataset_sha256": checksum,
        "dataset_version": dataset["dataset_version"],
        "dataset_source": "hand-authored synthetic, NOT independently reviewed Gold Dataset",
        "retrieval": "exact_cosine_scoped_numpy_not_qdrant_ann",
        "evaluation": results,
        "timings_ms": {
            "model_load": round(model_load_s * 1000, 2),
            "documents_batch_total": doc_encode_ms,
            "query_encode": percentiles_ms(query_ms),
            "per_query_exact_search": percentiles_ms(search_ms),
        },
        "memory_mb": {
            "process_rss_after_load": rss_loaded_mb,
            "process_rss_after_inference": round(process.memory_info().rss / 1048576, 2),
            "process_peak_rss_maxrss_linux": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2),
            "gpu_vram_measured": None,
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "gpu_available": bool(torch.cuda.is_available()),
            "torch": torch.__version__,
            "sentence_transformers": sentence_transformers.__version__,
            "transformers": transformers.__version__,
            "torch_num_threads": torch.get_num_threads(),
        },
        "ranking_ids": rankings,
        "not_measured": [
            "approved-domain-annotated-gold",
            "expert-relevance-judgments",
            "real-organization-GPU",
            "Qdrant-ANN-latency",
            "sparse-reranking",
            "legal-release-approval",
            "production-throughput",
            "final-acceptance-threshold",
        ],
    }
    del model
    gc.collect()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--dataset", type=Path, default=Path("benchmarks/phase07/gold_synthetic_v0.1.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run(args.model, args.dataset)
    except Exception as exc:
        # Never fabricate model metrics on failed downloads/inference.
        args.output.write_text(
            json.dumps(
                {
                    "status": "BLOCKED_OR_FAILED",
                    "candidate": args.model,
                    "error_type": type(exc).__name__,
                    "metrics": None,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "model": args.model,
        "revision": result["revision_full"],
        "metrics": result["evaluation"]["metrics"],
        "timings_ms": result["timings_ms"],
        "memory_mb": result["memory_mb"],
        "weights_sha256": result["weights_sha256"],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
