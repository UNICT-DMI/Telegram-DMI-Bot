from module.data.professor import Professor

def test_professor_table() -> None:
    professor = Professor()
    assert professor.table == "professors"

def test_professor_columns() -> None:
    professor = Professor()
    assert professor.columns == ("ID", "ruolo", "nome", "scheda_dmi", "fax", "telefono", "email", "ufficio", "sito") 
