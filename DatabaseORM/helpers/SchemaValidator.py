class SchemaError(Exception):
    pass

class SchemaValidator:

    def __init__(self, schema: dict, type_: str):
        self.schema = schema
        self.type_ = type_

    def _validateSchema(self):

        if self.type_ == 'create_table':

            # Validate keys of main schema
            for key in self.schema.keys():

                if not isinstance(key, str):
                    raise SchemaError(f"❌ Table name must be a string → {key}")

            # Validate each table
            for table, dataset in self.schema.items():

                if not isinstance(dataset, list):
                    raise SchemaError(f"❌ {table}: must be a list [columns, (optional) foreign_keys]")

                if len(dataset) < 1:
                    raise SchemaError(f"❌ {table}: must contain at least 1 element: columns")

                if len(dataset) > 2:
                    raise SchemaError(f"❌ {table}: must contain at most 2 elements: [columns, foreign_keys]")

                columns = dataset[0]
                foreign_keys = dataset[1] if len(dataset) == 2 else None

                # Validate columns dict
                if not isinstance(columns, dict):
                    raise SchemaError(f"❌ {table}: first element must be a dictionary of columns")

                col_errors = ""
                for col_name, options in columns.items():

                    if not isinstance(col_name, str):
                        col_errors += f"Column name must be a string → {col_name}\n"

                    if not isinstance(options, dict) or "__col_type__" not in options:
                        col_errors += f"{col_name}: must be a column function such as integer(), text(), enum(), etc.\n"

                if col_errors:
                    raise SchemaError(f"❌ Errors in columns of {table}:\n{col_errors}")

                # Validate foreign keys block
                if foreign_keys is not None:

                    if not isinstance(foreign_keys, dict):
                        raise SchemaError(f"❌ {table}: second element must be a dictionary of foreign keys")

                    if len(foreign_keys) == 0:
                        raise SchemaError(f"❌ {table}: foreign key block cannot be empty")

                    fk_errors = ""

                    for cons, tpl in foreign_keys.items():

                        if not isinstance(cons, str):
                            fk_errors += f"FK key must be a string → {cons}\n"

                        if not isinstance(tpl, tuple):
                            fk_errors += f"{cons}: must be a tuple\n"
                            continue

                        if len(tpl) != 3:
                            fk_errors += f"{cons}: must contain (column_src, table_dest, column_dest)\n"

                    if fk_errors:
                        raise SchemaError(f"❌ Errors in foreign keys of {table}:\n{fk_errors}")
