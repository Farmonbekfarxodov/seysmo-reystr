from django.db import migrations


def _compute_report_code(category, journal_scope, conference_scope, local_conf_level,
                          participation_scope, publication_type, patent_category):
    """Standalone duplicate of specialists.report_codes.compute_report_code,
    operating on plain values instead of a model instance -- migrations
    must never import current application code, since that code can
    change independently of already-applied migration history."""
    if category in ("foreign_article", "local_article"):
        return {
            "scopus_wos": "2.1", "other_foreign": "2.2", "cis": "2.3", "local": "2.4",
        }.get(journal_scope, "")
    if category == "thesis":
        if conference_scope == "scopus_wos":
            return "3.1"
        if conference_scope == "other_foreign":
            return "3.2"
        if conference_scope == "cis":
            return "3.3"
        if conference_scope == "local":
            return {"international": "3.4.1", "republic": "3.4.2"}.get(local_conf_level, "")
        return ""
    if category == "conference_participation":
        return {"foreign": "4.1", "republic": "4.2"}.get(participation_scope, "")
    if category == "other_publication":
        return {"monograph": "5.1", "textbook": "5.3", "manual": "5.5"}.get(publication_type, "")
    if category == "patent":
        return {
            "invention": "6.1", "foreign_patent": "6.2", "utility_model": "6.3",
            "patent_application": "6.4", "trademark": "6.5",
            "software_certificate": "6.6", "license_agreement": "6.7",
        }.get(patent_category, "")
    return ""


# Old index_type -> (journal_scope, indexed_in). Values not in this map
# (including blank) are left unclassified -- never guessed.
_INDEX_TYPE_MAP = {
    "scopus": ("scopus_wos", "scopus"),
    "wos": ("scopus_wos", "wos"),
    "scopus_wos": ("scopus_wos", "both"),
    "other_intl": ("other_foreign", ""),
}

# Old thesis_category -> (conference_scope, local_conf_level). The old
# system had no way to express "abroad" for a thesis at all -- every old
# thesis record is treated as a local/mahalliy conference, since that's
# the most that the old data actually encoded.
_THESIS_CATEGORY_MAP = {
    "international_conf": ("local", "international"),
    "republic_conf": ("local", "republic"),
}


def migrate_taxonomy(apps, schema_editor):
    ScientificWork = apps.get_model("specialists", "ScientificWork")

    for work in ScientificWork.objects.all():
        journal_scope = ""
        indexed_in = ""
        conference_scope = ""
        local_conf_level = ""
        new_patent_category = ""
        publication_type = ""
        new_category = work.category

        if work.category == "foreign_article":
            journal_scope, indexed_in = _INDEX_TYPE_MAP.get(work.index_type, ("", ""))

        elif work.category == "local_article":
            journal_scope = "local"  # always determinable, per the new spec

        elif work.category == "thesis":
            conference_scope, local_conf_level = _THESIS_CATEGORY_MAP.get(work.thesis_category, ("", ""))

        elif work.category == "patent":
            old_cat = work.patent_category
            is_foreign = work.patent_type == "foreign"
            if old_cat == "invention":
                new_patent_category = "foreign_patent" if is_foreign else "invention"
            elif old_cat == "utility_model":
                new_patent_category = "foreign_patent" if is_foreign else "utility_model"
            elif old_cat == "software_cert":
                # A foreign software certificate doesn't clearly map to
                # "Xorijiy patent" (6.2) or stay 6.6 -- genuinely
                # undetermined, so leave unclassified rather than guess.
                new_patent_category = "" if is_foreign else "software_certificate"
            # old "industrial_design" (Sanoat namunasi) has NO equivalent
            # in the new 7-value official list at all -- always left
            # unclassified, regardless of local/foreign.

        elif work.category == "monograph":
            new_category = "other_publication"
            publication_type = "monograph"  # the old category WAS always this

        report_code = _compute_report_code(
            new_category, journal_scope, conference_scope, local_conf_level,
            "", publication_type, new_patent_category,
        )

        ScientificWork.objects.filter(pk=work.pk).update(
            category=new_category,
            journal_scope=journal_scope,
            indexed_in=indexed_in,
            conference_scope=conference_scope,
            local_conf_level=local_conf_level,
            patent_category=new_patent_category if work.category == "patent" else work.patent_category,
            publication_type=publication_type,
            published_abroad=False,
            report_code=report_code,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("specialists", "0006_add_report_taxonomy_fields"),
    ]

    operations = [
        migrations.RunPython(migrate_taxonomy, noop_reverse),
    ]
