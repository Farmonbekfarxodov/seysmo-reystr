import os

from django.db import migrations


def copy_documents_to_works(apps, schema_editor):
    SpecialistDocument = apps.get_model("specialists", "SpecialistDocument")
    ScientificWork = apps.get_model("specialists", "ScientificWork")

    for doc in SpecialistDocument.objects.all():
        # No title existed before -- use the original filename (extension
        # stripped) as a reasonable starting point; the employee can edit
        # it afterward. Year comes from the upload date.
        title = os.path.splitext(doc.original_filename)[0] or doc.original_filename

        work = ScientificWork.objects.create(
            specialist_id=doc.specialist_id,
            category="local_article",
            title=title,
            year=doc.uploaded_at.year,
            file=doc.file.name,
            original_filename=doc.original_filename,
            size=doc.size,
        )
        # auto_now_add ignores any value passed to create(); .update()
        # bypasses that field's pre_save() override so we can backdate it.
        ScientificWork.objects.filter(pk=work.pk).update(created_at=doc.uploaded_at)


def noop_reverse(apps, schema_editor):
    # Not reversible -- SpecialistDocument rows are gone by the time this
    # migration would be unapplied (a later migration drops the table).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("specialists", "0002_alter_specialistprofile_is_public_scientificwork"),
    ]

    operations = [
        migrations.RunPython(copy_documents_to_works, noop_reverse),
    ]
