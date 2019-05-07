from pynonymizer.database import get_temp_db_name

def test_uniqueness():
    """
    Generate 100 temp db names, and test if they're unique.
    """
    db_names = [get_temp_db_name("filename.sql") for i in range(100)]
    assert len(db_names) == len(set(db_names))

