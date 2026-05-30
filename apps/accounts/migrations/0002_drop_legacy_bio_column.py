from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE accounts_profile DROP COLUMN IF EXISTS bio;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
