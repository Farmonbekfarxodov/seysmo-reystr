"""Everything about turning ScientificWork rows into the official annual
report. Kept as pure functions (no DB writes except the report_code
assignment itself) so the counting/dedup rules are easy to unit test."""

import re
from collections import defaultdict


def compute_report_code(work):
    """Derive the report line code for a single record. Returns "" when
    the record can't yet be classified (missing required fields) -- such
    records are excluded from all report counts and flagged as
    unclassified rather than guessed at."""
    Category = work.__class__.Category

    if work.category in (Category.FOREIGN_ARTICLE, Category.LOCAL_ARTICLE):
        return {
            "scopus_wos": "2.1",
            "other_foreign": "2.2",
            "cis": "2.3",
            "local": "2.4",
        }.get(work.journal_scope, "")

    if work.category == Category.THESIS:
        scope = work.conference_scope
        if scope == "scopus_wos":
            return "3.1"
        if scope == "other_foreign":
            return "3.2"
        if scope == "cis":
            return "3.3"
        if scope == "local":
            return {"international": "3.4.1", "republic": "3.4.2"}.get(work.local_conf_level, "")
        return ""

    if work.category == Category.CONFERENCE_PARTICIPATION:
        return {"foreign": "4.1", "republic": "4.2"}.get(work.participation_scope, "")

    if work.category == Category.OTHER_PUBLICATION:
        return {
            "monograph": "5.1",
            "textbook": "5.3",
            "manual": "5.5",
        }.get(work.publication_type, "")

    if work.category == Category.PATENT:
        return {
            "invention": "6.1",
            "foreign_patent": "6.2",
            "utility_model": "6.3",
            "patent_application": "6.4",
            "trademark": "6.5",
            "software_certificate": "6.6",
            "license_agreement": "6.7",
        }.get(work.patent_category, "")

    return ""


# Report structure: sections in order, each with its numbered lines.
# `is_subset` lines are NOT included in `total_codes` (their parent's
# sibling total already covers them structurally, per the spec's explicit
# "jumladan" rule) -- 3.4 is special: no record ever gets exactly "3.4",
# only "3.4.1"/"3.4.2"; the "3.4" total is their sum, and IS included in
# section III's total.
REPORT_STRUCTURE = [
    {
        "id": "II",
        "title": "Ilmiy jurnallarda chop etilgan maqolalar soni",
        "lines": [
            {"code": "2.1", "label": "Scopus va/yoki Web of Science bazasiga kiritilgan jurnallarda"},
            {"code": "2.2", "label": "Boshqa xorijiy jurnallarda"},
            {"code": "2.3", "label": "MDH jurnallarida"},
            {"code": "2.4", "label": "Mahalliy jurnallarda"},
        ],
        "total_codes": ["2.1", "2.2", "2.3", "2.4"],
    },
    {
        "id": "III",
        "title": "Ilmiy-amaliy anjumanlar va boshqa ilmiy to'plamlarda chop etilgan nashrlar soni",
        "lines": [
            {"code": "3.1", "label": "Scopus va/yoki Web of Science bazasiga kiritilgan anjumanlar materiallari to'plami"},
            {"code": "3.2", "label": "Xorijda o'tkazilgan boshqa anjumanlarda"},
            {"code": "3.3", "label": "MDH davlatlarida o'tkazilgan anjumanlarda"},
            {"code": "3.4", "label": "Mahalliy o'tkazilgan anjumanlarda, jumladan:", "is_group": True},
            {"code": "3.4.1", "label": "Xalqaro anjumanlarda", "is_subset": True, "parent": "3.4"},
            {"code": "3.4.2", "label": "Respublikada o'tkazilgan anjumanlarda", "is_subset": True, "parent": "3.4"},
        ],
        "total_codes": ["3.1", "3.2", "3.3", "3.4"],
    },
    {
        "id": "IV",
        "title": "Ilmiy anjumanlarda ma'ruza bilan ishtirok soni (og'zaki, plenar) — sertifikatlar asosida",
        "lines": [
            {"code": "4.1", "label": "Xorijiy anjumanlarda"},
            {"code": "4.2", "label": "Respublikada anjumanlarda"},
        ],
        "total_codes": ["4.1", "4.2"],
    },
    {
        "id": "V",
        "title": "Boshqa nashrlar",
        "lines": [
            {"code": "5.1", "label": "Monografiyalar"},
            {"code": "5.2", "label": "Jumladan, xorijda chiqqan monografiya", "is_subset": True, "parent": "5.1"},
            {"code": "5.3", "label": "Darsliklar"},
            {"code": "5.4", "label": "Jumladan, xorijda chiqqan darsliklar", "is_subset": True, "parent": "5.3"},
            {"code": "5.5", "label": "O'quv qo'llanmalar"},
        ],
        "total_codes": ["5.1", "5.3", "5.5"],
    },
    {
        "id": "VI",
        "title": "Respublika Intellektual mulk agentligida ro'yxatdan o'tgan hujjatlar soni",
        "lines": [
            {"code": "6.1", "label": "Olingan patentlar (Ixtiro) soni"},
            {"code": "6.2", "label": "Xorijiy patent"},
            {"code": "6.3", "label": "Foydali modelga patent"},
            {"code": "6.4", "label": "Patent uchun talabnoma"},
            {"code": "6.5", "label": "Tovar belgisi"},
            {"code": "6.6", "label": "Kompyuter dasturiy mahsulotlari guvohnomalari"},
            {"code": "6.7", "label": "Tuzilgan litsenziya shartnomalari soni"},
        ],
        "total_codes": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7"],
    },
]

ALL_LEAF_CODES = [
    "2.1", "2.2", "2.3", "2.4",
    "3.1", "3.2", "3.3", "3.4.1", "3.4.2",
    "4.1", "4.2",
    "5.1", "5.3", "5.5",
    "6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7",
]


def build_report(works):
    """works: an iterable of ScientificWork instances (already filtered to
    the desired scope -- one employee, one year, etc; NOT necessarily a
    QuerySet, since institute reports pass in a deduplicated Python list).
    Returns the full structured report dict."""
    works = list(works)

    counts = defaultdict(int)
    unclassified = []
    for w in works:
        if not w.report_code:
            unclassified.append(w)
            continue
        counts[w.report_code] += 1

    # 5.2 / 5.4 are derived from published_abroad, not report_code.
    subset_abroad_counts = {"5.2": 0, "5.4": 0}
    for w in works:
        if w.report_code == "5.1" and w.published_abroad:
            subset_abroad_counts["5.2"] += 1
        if w.report_code == "5.3" and w.published_abroad:
            subset_abroad_counts["5.4"] += 1

    def line_count(code):
        if code == "3.4":
            return counts.get("3.4.1", 0) + counts.get("3.4.2", 0)
        if code in subset_abroad_counts:
            return subset_abroad_counts[code]
        return counts.get(code, 0)

    sections = []
    for section in REPORT_STRUCTURE:
        lines = []
        for line in section["lines"]:
            lines.append({
                "code": line["code"],
                "label": line["label"],
                "count": line_count(line["code"]),
                "is_subset": line.get("is_subset", False),
                "is_group": line.get("is_group", False),
                "parent_code": line.get("parent"),
            })
        total = sum(line_count(code) for code in section["total_codes"])
        sections.append({"id": section["id"], "title": section["title"], "lines": lines, "total": total})

    # Quartile matrix for line 2.1.
    quartile_matrix = {
        "scopus": {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0},
        "wos": {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0},
    }
    for w in works:
        if w.report_code != "2.1":
            continue
        if w.indexed_in in ("scopus", "both") and w.scopus_quartile:
            quartile_matrix["scopus"][w.scopus_quartile] += 1
        if w.indexed_in in ("wos", "both") and w.wos_quartile:
            quartile_matrix["wos"][w.wos_quartile] += 1

    # Certificate-less conference participations (informational footnote).
    without_certificate = sum(
        1 for w in works
        if w.category == "conference_participation" and w.report_code and not w.file
    )

    return {
        "sections": sections,
        "quartile_matrix": quartile_matrix,
        "unclassified": unclassified,
        "without_certificate": without_certificate,
        "total_records": len(works),
    }


# ---------------------------------------------------------------------------
# Institute-wide de-duplication
# ---------------------------------------------------------------------------

_DOI_PREFIXES = ("https://doi.org/", "http://doi.org/", "doi.org/", "doi:")


def normalize_doi(doi: str) -> str:
    d = (doi or "").strip().lower()
    for prefix in _DOI_PREFIXES:
        if d.startswith(prefix):
            d = d[len(prefix):]
            break
    return d.strip().strip("/")


def normalize_signature(work) -> str:
    title = re.sub(r"[^\w\s]", "", (work.title or "").lower())
    title = re.sub(r"\s+", " ", title).strip()
    return f"{work.category}|{title}|{work.report_year or ''}"


def dedup_key(work) -> str:
    doi = normalize_doi(work.doi)
    return f"doi:{doi}" if doi else f"sig:{normalize_signature(work)}"


def deduplicate_works(works):
    """Groups records that represent the "same" work (by normalized DOI,
    falling back to a title+category+year signature) so institute-wide
    totals count each real output once. Returns (deduped_list,
    merged_groups) where merged_groups only contains groups with >1
    member (for the "N ta takroriy yozuv birlashtirildi" drill-down)."""
    groups = defaultdict(list)
    for w in works:
        groups[dedup_key(w)].append(w)

    deduped = [members[0] for members in groups.values()]
    merged_groups = [members for members in groups.values() if len(members) > 1]
    return deduped, merged_groups


def deduplicate_works_full(works):
    """Like deduplicate_works, but returns (deduped_list, groups_by_id)
    where groups_by_id maps EVERY representative's pk to its full member
    list (including groups of 1) -- needed to show every co-author on a
    deduplicated line's drill-down row, not just the flagged duplicates."""
    groups = defaultdict(list)
    for w in works:
        groups[dedup_key(w)].append(w)

    deduped = [members[0] for members in groups.values()]
    groups_by_id = {members[0].pk: members for members in groups.values()}
    return deduped, groups_by_id


# ---------------------------------------------------------------------------
# Drill-down: the exact records behind one report line / quartile cell /
# section total. MUST stay in lockstep with build_report()'s counting so a
# modal's row count always equals the number shown on the report.
# ---------------------------------------------------------------------------

_SECTION_TOTAL_EXPANDED_CODES = {
    section["id"]: {c for code in section["total_codes"] for c in (["3.4.1", "3.4.2"] if code == "3.4" else [code])}
    for section in REPORT_STRUCTURE
}


def resolve_line_records(works, code):
    """works: already-scoped (and, for institute reports, already
    deduplicated) list of ScientificWork instances -- the same list
    passed to build_report(). code: a leaf report_code ("2.1"), the
    combined local-conference code ("3.4"), a subset code ("5.2"/"5.4"),
    a quartile-qualified article code ("2.1:scopus:Q1"), or a section id
    for its "Jami" total ("II".."VI")."""
    works = list(works)

    if code in _SECTION_TOTAL_EXPANDED_CODES:
        expanded = _SECTION_TOTAL_EXPANDED_CODES[code]
        return [w for w in works if w.report_code in expanded]

    if ":" in code:
        base, db, quartile = code.split(":")
        field = "scopus_quartile" if db == "scopus" else "wos_quartile"
        indexed_values = ("scopus", "both") if db == "scopus" else ("wos", "both")
        return [
            w for w in works
            if w.report_code == base and w.indexed_in in indexed_values and getattr(w, field) == quartile
        ]

    if code == "3.4":
        return [w for w in works if w.report_code in ("3.4.1", "3.4.2")]

    if code == "5.2":
        return [w for w in works if w.report_code == "5.1" and w.published_abroad]

    if code == "5.4":
        return [w for w in works if w.report_code == "5.3" and w.published_abroad]

    return [w for w in works if w.report_code == code]


def line_label(code):
    """Human label for a modal header, e.g. "2.1", "V", "2.1:scopus:Q1"."""
    for section in REPORT_STRUCTURE:
        if section["id"] == code:
            return f"{code}. {section['title']} — Jami"
        for line in section["lines"]:
            if line["code"] == code:
                return f"{code} — {line['label']}"
    if ":" in code:
        base, db, quartile = code.split(":")
        db_label = "Scopus" if db == "scopus" else "Web of Science"
        return f"{base} — {db_label} {quartile}"
    return code
