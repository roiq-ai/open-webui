from sqlalchemy import Inspector


def get_existing_tables(op):
    con = op.get_bind()
    inspector = Inspector.from_engine(con)
    tables = set(inspector.get_table_names())
    return tables
