import specialists.models
import specialists.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('specialists', '0005_merge_20260721_0527'),
    ]

    operations = [
        migrations.AddField(
            model_name='scientificwork',
            name='conference_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='conference_scope',
            field=models.CharField(blank=True, choices=[('scopus_wos', "Scopus/WoS to'plami"), ('other_foreign', 'Boshqa xorijiy anjuman'), ('cis', 'MDH anjumani'), ('local', 'Mahalliy anjuman')], max_length=20),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='event_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='indexed_in',
            field=models.CharField(blank=True, choices=[('scopus', 'Scopus'), ('wos', 'Web of Science'), ('both', 'Scopus va Web of Science')], max_length=10),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='journal_scope',
            field=models.CharField(blank=True, choices=[('scopus_wos', 'Scopus va/yoki Web of Science bazasiga kiritilgan'), ('other_foreign', 'Boshqa xorijiy jurnal'), ('cis', 'MDH jurnali'), ('local', 'Mahalliy jurnal')], max_length=20),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='local_conf_level',
            field=models.CharField(blank=True, choices=[('international', 'Xalqaro anjuman'), ('republic', 'Respublika anjumani')], max_length=20),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='location',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='participation_scope',
            field=models.CharField(blank=True, choices=[('foreign', 'Xorijiy'), ('republic', 'Respublika')], max_length=20),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='presentation_type',
            field=models.CharField(blank=True, choices=[('oral', "Og'zaki"), ('plenary', 'Plenar')], max_length=20),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='publication_type',
            field=models.CharField(blank=True, choices=[('monograph', 'Monografiya'), ('textbook', 'Darslik'), ('manual', "O'quv qo'llanma")], max_length=20),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='published_abroad',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='report_code',
            field=models.CharField(blank=True, db_index=True, max_length=10),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='scopus_quartile',
            field=models.CharField(blank=True, choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4')], max_length=2),
        ),
        migrations.AddField(
            model_name='scientificwork',
            name='wos_quartile',
            field=models.CharField(blank=True, choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4')], max_length=2),
        ),
        migrations.AlterField(
            model_name='scientificwork',
            name='category',
            field=models.CharField(choices=[('foreign_article', 'Xorijiy maqola'), ('local_article', 'Mahalliy maqola'), ('thesis', 'Tezis'), ('conference_participation', 'Anjumanda ishtirok'), ('patent', 'Patent'), ('other_publication', 'Boshqa nashr')], max_length=30),
        ),
        migrations.AlterField(
            model_name='scientificwork',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=specialists.models.work_upload_path, validators=[specialists.validators.validate_uploaded_document]),
        ),
        migrations.AlterField(
            model_name='scientificwork',
            name='original_filename',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='scientificwork',
            name='patent_category',
            field=models.CharField(blank=True, choices=[('invention', 'Ixtiro (patent)'), ('foreign_patent', 'Xorijiy patent'), ('utility_model', 'Foydali modelga patent'), ('patent_application', 'Patent uchun talabnoma'), ('trademark', 'Tovar belgisi'), ('software_certificate', 'Dasturiy mahsulot guvohnomasi'), ('license_agreement', 'Litsenziya shartnomasi')], max_length=30),
        ),
        migrations.AlterField(
            model_name='scientificwork',
            name='size',
            field=models.PositiveIntegerField(blank=True, help_text='File size in bytes', null=True),
        ),
    ]
