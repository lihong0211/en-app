import sqlalchemy


def check_data_many(data):
    many = False
    print(type(data))
    if isinstance(data, list):
        many = True
    if isinstance(data, sqlalchemy.engine.cursor.CursorResult):
        many = True
    return many
