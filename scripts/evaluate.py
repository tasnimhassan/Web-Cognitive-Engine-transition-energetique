"""Evalue le moteur sur docs/validation_questions.json.
Usage :  python -m scripts.evaluate            (recherche seule, rapide)
         python -m scripts.evaluate --llm      (+ reponse du LLM, Ollama requis)
         python -m scripts.evaluate --k 8"""
import argparse
import json

from src.config import ROOT, TOP_K
from src.search import search


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=TOP_K)
    ap.add_argument("--llm", action="store_true")
    args = ap.parse_args()
    questions = json.loads((ROOT / "docs" / "validation_questions.json").read_text(encoding="utf-8"))

    results, hits, total = [], 0, 0
    for q in questions:
        passages = search(q["question"], args.k)
        files = [p["source_file"] for p in passages]
        row = {"id": q["id"], "question": q["question"], "retrieved": files, "scores": [p["score"] for p in passages]}
        if q["expected_sources"]:
            total += 1
            rank = next((i for i, f in enumerate(files, 1) if f in q["expected_sources"]), None)
            row["rank_of_good_source"] = rank
            hits += rank is not None
            print(f"[{'OK' if rank else 'X '}] Q{q['id']} bonne source au rang {rank}" if rank else f"[X ] Q{q['id']} bonne source absente du Top-{args.k}")
        else:
            row["out_of_corpus_best_score"] = row["scores"][0] if row["scores"] else None
            print(f"[--] Q{q['id']} hors corpus : meilleur score = {row['scores'][0] if row['scores'] else 'aucun'}")
        if args.llm:
            from src.rag import answer
            a = answer(q["question"], args.k)["answer"]
            row["answer"] = a
            if q["keywords"]:
                row["keyword_found"] = any(k in a for k in q["keywords"])
                print("     mot-cle attendu dans la reponse :", "oui" if row["keyword_found"] else "NON")
            print("     ->", a[:200].replace("\n", " "))
        results.append(row)

    print(f"\nRecherche : {hits}/{total} questions avec la bonne source dans le Top-{args.k}")
    (ROOT / "docs" / "evaluation_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Resultats detailles : docs/evaluation_results.json")


if __name__ == "__main__":
    main()
