""" Peewee migrations. """

import datetime as dt
import peewee as pw


def migrate(migrator, database, **kwargs):
    """ Write your migrations here.

    > migrator.create_table(model)
    > migrator.drop_table(model, cascade=True)
    > migrator.add_columns(model, **fields)
    > migrator.drop_columns(models, *names, cascade=True)
    > migrator.rename_column(model, old_name, new_name)
    > migrator.rename_table(model, new_name)
    > migrator.add_index(model, *columns, unique=False)
    > migrator.drop_index(model, index_name)
    > migrator.add_not_null(model, name)
    > migrator.drop_not_null(model, name)

    """
    from mixer.backend.peewee import Mixer
    from muffin.utils import generate_password_hash

    mixer = Mixer(commit=True)
    model = migrator.orm['user']
    mixer.blend(model, username='user', email='user@muffin.io',
                password=generate_password_hash('pass'))
