from src.analytics import build_analytics, count_keywords, family_of, histogram, pca_2d


def test_family_of():
    assert family_of("rte_bilan_occitanie_2025.pdf") == "RTE"
    assert family_of("wiki_energie_solaire_france.txt") == "Wikipédia"
    assert family_of("rte_bp2025_banque_des_territoires.html") == "Presse spécialisée"
    assert family_of("inconnu.pdf") == "Autres"


def test_count_keywords():
    c = count_keywords("L'éolien et le solaire progressent ; le nucléaire reste stable. La PPE3 fixe les objectifs d'éolien.")
    assert c["éolien"] == 2 and c["solaire"] == 1 and c["nucléaire"] == 1 and c["PPE"] == 1 and c["hydrogène"] == 0


def test_histogram():
    h = histogram([10, 60, 70, 480, 900], width=50, top=550)
    assert h[0]["value"] == 1 and h[1]["value"] == 2 and h[-1]["value"] == 1 and sum(b["value"] for b in h) == 5


def test_build_analytics_and_pca():
    docs = [{"source_file": "rte_a.pdf", "format": "pdf", "n_chars": 100, "text": "solaire solaire éolien"},
            {"source_file": "wiki_b.txt", "format": "txt", "n_chars": 300, "text": "nucléaire"}]
    chunks = [{"text": "x" * 120, "source_file": "rte_a.pdf", "page": 1}, {"text": "y" * 480, "source_file": "wiki_b.txt", "page": 1},
              {"text": "z" * 300, "source_file": "wiki_b.txt", "page": 2}]
    vecs = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    out = build_analytics(docs, chunks, vecs)
    assert out["totals"] == {"documents": 2, "chunks": 3, "chars": 400, "avg_chunk": 300.0}
    assert {f["label"]: f["value"] for f in out["formats"]} == {"PDF": 1, "TXT": 1}
    assert out["keywords"][0]["label"] == "solaire" and out["keywords"][0]["value"] == 2
    assert out["volume"][0]["label"] == "wiki_b.txt"
    assert len(out["pca"]["points"]) == 3 and all(0 <= p["x"] <= 1 for p in out["pca"]["points"])
