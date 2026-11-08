"""Etape 8 - Recette : test global de l'application, de l'ingestion au chat et a la dataviz.

Prerequis : l'API tourne (python -m uvicorn src.api:app) et la base est indexee.
Usage :  python -m scripts.recette              (complet, avec le LLM Ollama)
         python -m scripts.recette --no-llm     (sans appeler le LLM)
         python -m scripts.recette --base-url http://127.0.0.1:8000 --k 5
Resultat : affichage console + docs/rapport_recette.md (a joindre au rendu)."""
import argparse
import json
import sys
import time
from datetime import datetime

import requests

from src.config import PROCESSED_DIR, RAW_DIR, ROOT

FORMATS = {".pdf", ".html", ".htm", ".docx", ".txt"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    checks = []          # (nom, ok, detail)

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        print(f"[{'OK' if ok else 'ECHEC'}] {name}" + (f" : {detail}" if detail else ""))

    def get(path, **kw):
        return requests.get(base + path, timeout=30, **kw)

    def post(path, payload, timeout=600):
        return requests.post(base + path, json=payload, timeout=timeout)

    print("=== 1. Corpus et ingestion ===")
    raw = [p for p in RAW_DIR.iterdir() if p.suffix.lower() in FORMATS]
    fmts = sorted({p.suffix.lower().lstrip(".") for p in raw})
    check("Corpus de 30 a 50 documents", 30 <= len(raw) <= 50, f"{len(raw)} documents")
    check("Au moins 3 formats differents", len(fmts) >= 3, ", ".join(fmts))
    processed = list(PROCESSED_DIR.glob("*.json"))
    check("Documents nettoyes (data/processed)", len(processed) >= len(raw) - 2, f"{len(processed)} JSON")

    print("\n=== 2. API et base vectorielle ===")
    try:
        check("API en marche (/health)", get("/health").json().get("status") == "ok")
    except Exception as e:
        check("API en marche (/health)", False, f"injoignable ({e}). Lance : python -m uvicorn src.api:app")
        return finish(checks, [], args)
    st = get("/stats").json()
    check("Base indexee (/stats)", st["n_chunks"] > 0 and st["n_documents"] >= 30,
          f"{st['n_documents']} documents, {st['n_chunks']} passages")

    print("\n=== 3. Dataviz ===")
    try:
        an = get("/analytics", params={"refresh": "true"}).json()
        check("Tableau de bord (/analytics)", an["totals"]["chunks"] == st["n_chunks"],
              f"{len(an['formats'])} formats, {len(an['keywords'])} mots-cles")
        check("Carte ACP des passages", an.get("pca") is not None and len(an["pca"]["points"]) == st["n_chunks"])
    except Exception as e:
        check("Tableau de bord (/analytics)", False, str(e))

    print("\n=== 4. Interface web ===")
    html = get("/").text
    check("Page de chat servie (/)", "WebCognitive" in html and "tab-dash" in html)

    llm_ok = False
    if not args.no_llm:
        ls = get("/llm/status").json()
        llm_ok = ls["ollama"] and ls["model_available"]
        check("Ollama et modele disponibles", llm_ok, ls["model"] if llm_ok else "lance Ollama et : ollama pull " + ls["model"])

    print("\n=== 5. Questions de validation ===")
    questions = json.loads((ROOT / "docs" / "validation_questions.json").read_text(encoding="utf-8"))
    rows, hits, total, kw_hits, kw_total = [], 0, 0, 0, 0
    for q in questions:
        row = {"id": q["id"], "question": q["question"], "rank": None, "answer": "", "kw": None, "sec": None}
        res = post("/search", {"question": q["question"], "k": args.k}).json()["results"]
        files = [r["source_file"] for r in res]
        if q["expected_sources"]:
            total += 1
            row["rank"] = next((i for i, f in enumerate(files, 1) if f in q["expected_sources"]), None)
            hits += row["rank"] is not None
        if not args.no_llm and llm_ok:
            t0 = time.time()
            try:
                a = post("/chat", {"question": q["question"], "k": args.k}).json()["answer"]
            except Exception as e:
                a = f"(erreur : {e})"
            row["sec"] = round(time.time() - t0, 1)
            row["answer"] = a
            if q["keywords"]:
                kw_total += 1
                row["kw"] = any(k in a for k in q["keywords"])
                kw_hits += row["kw"]
            if not q["expected_sources"]:
                row["refus"] = "ne sais pas" in a.lower()
        rows.append(row)
        tag = "hors corpus" if not q["expected_sources"] else (f"source au rang {row['rank']}" if row["rank"] else "source ABSENTE")
        print(f"  Q{q['id']} : {tag}" + (f" | {row['sec']} s" if row["sec"] else ""))

    check(f"Recherche : bonne source dans le Top-{args.k}", total == 0 or hits / total >= 0.7, f"{hits}/{total}")
    if llm_ok:
        check("Reponses : mot-cle attendu present", kw_total == 0 or kw_hits / kw_total >= 0.5, f"{kw_hits}/{kw_total}")
        out = [r for r in rows if "refus" in r]
        check("Question hors corpus : le systeme refuse de repondre", all(r["refus"] for r in out) if out else True,
              "correct" if out and all(r["refus"] for r in out) else "")
    finish(checks, rows, args)


def finish(checks, rows, args):
    ok = sum(1 for _, o, _ in checks if o)
    print(f"\nRESULTAT : {ok}/{len(checks)} controles reussis")
    lines = ["# Rapport de recette - WebCognitive Engine", "",
             f"Date : {datetime.now():%d/%m/%Y %H:%M}  |  Top-K : {args.k}  |  LLM : {'non teste' if args.no_llm else 'teste'}", "",
             f"**Resultat global : {ok}/{len(checks)} controles reussis**", "",
             "## Controles", "", "| Controle | Statut | Detail |", "|---|---|---|"]
    lines += [f"| {n} | {'OK' if o else 'ECHEC'} | {d} |" for n, o, d in checks]
    if rows:
        lines += ["", "## Questions de validation", "", "| # | Question | Rang de la bonne source | Mot-cle | Temps (s) |", "|---|---|---|---|---|"]
        for r in rows:
            kw = "-" if r["kw"] is None else ("oui" if r["kw"] else "non")
            lines.append(f"| {r['id']} | {r['question']} | {r['rank'] or '-'} | {kw} | {r['sec'] or '-'} |")
        if any(r["answer"] for r in rows):
            lines += ["", "## Reponses du systeme", ""]
            for r in rows:
                if r["answer"]:
                    lines += [f"**Q{r['id']}. {r['question']}**", "", "> " + r["answer"].replace("\n", "\n> "), ""]
    (ROOT / "docs" / "rapport_recette.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Rapport ecrit : docs/rapport_recette.md")
    sys.exit(0 if ok == len(checks) else 1)


if __name__ == "__main__":
    main()
