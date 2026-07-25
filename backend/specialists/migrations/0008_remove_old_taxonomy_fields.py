from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialists', '0007_migrate_report_taxonomy_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scientificwork',
            name='index_type',
        ),
        migrations.RemoveField(
            model_name='scientificwork',
            name='patent_type',
        ),
        migrations.RemoveField(
            model_name='scientificwork',
            name='thesis_category',
        ),
    ]
