from src.chunking import chunk_text
from src.ingestion.cleaning import clean_text, fix_encoding


def test_multiple_spaces_and_newlines():
    assert clean_text("Bonjour   le\nmonde  entier.") == "Bonjour le monde entier."


def test_paragraphs_kept():
    assert clean_text("Para un.\n\nPara deux.") == "Para un.\n\nPara deux."


def test_hyphenation_and_page_numbers():
    out = clean_text("La protec-\ntion des donnees\n12\nest essentielle.")
    assert "protection" in out and "12" not in out


def test_mojibake():
    assert fix_encoding("donnÃ©es personnelles") == "données personnelles"


def test_ligatures():
    assert "fi" in clean_text("\ufb01chier")


def test_chunk_size_and_overlap():
    text = ". ".join(f"Phrase numero {i} sur la protection des donnees" for i in range(60))
    chunks = chunk_text(text, size=300, overlap=60)
    assert len(chunks) > 3
    assert all(len(c) <= 300 for c in chunks)
    # chevauchement : la fin d'un chunk reapparait au debut du suivant
    tail = chunks[0].split()[-3:]
    assert " ".join(tail) in chunks[1]


def test_short_text_single_chunk():
    assert chunk_text("Court.", 500, 100) == ["Court."]
