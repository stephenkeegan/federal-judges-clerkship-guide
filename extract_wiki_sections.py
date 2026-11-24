"""
Extract structured information from Wikipedia summaries.

Parses the Wikipedia Summary text to extract:
- Education: undergraduate school, law school, degrees
- Clerkships: judges they clerked for
- Career: previous positions (AUSA, private practice, state court, etc.)
- Notable cases: cases they presided over
- Appointment details: who appointed them, when confirmed

This fills in:
- Wiki_Education
- Wiki_Clerkships
- Wiki_Career
- Education (structured)
- Alma mater
"""

import pandas as pd
import numpy as np
import re


# Patterns for extracting education
EDU_PATTERNS = [
    # "received a Bachelor of Arts from Harvard University"
    r"received?\s+(?:a\s+)?(?:Bachelor|Master|Doctor|Juris|J\.D\.|B\.A\.|J\.D\.|M\.A\.|Ph\.D\.|LL\.B\.|LL\.M\.)[^.]*?from\s+([^,.]+(?:\s+[A-Z][a-z]+)*)",
    # "graduated from Yale Law School"
    r"graduated\s+from\s+([^,.]+(?:\s+[A-Z][a-z]+)*)",
    # "earned [a] Bachelor of Arts degree from Princeton University"
    r"earned?\s+(?:a\s+)?(?:Bachelor|Master|Doctor|Juris)[^.]*?from\s+([^,.]+)",
    # "attended Harvard University" / "studied at Yale"
    r"attended\s+([^,.]+(?:\s+[A-Z][a-z]+)*)",
    # "received his J.D. from Harvard Law School"
    r"(?:his|her|J\.D\.|law degree)\s+from\s+([^,.]+)",
    # "A.B. from Princeton University"
    r"(?:A\.B\.|B\.A\.|J\.D\.|LL\.B\.)\s+from\s+([^,.]+)",
    # "degree from University of Chicago Law School"
    r"degree\s+from\s+([^,.]+)",
]

# Law school specific patterns
LAW_SCHOOL_PATTERNS = [
    r"law\s+school\s+(?:at|from)\s+([^,.]+)",
    r"J\.D\.\s+from\s+([^,.]+)",
    r"law\s+degree\s+from\s+([^,.]+)",
    r"received\s+(?:his|her)\s+(?:law\s+)?degree\s+from\s+([^,.]+)",
    r"graduated\s+from\s+([^,.]*?(?:Law|School))",
    r"attended\s+([^,.]*?(?:Law|School))",
]

# Clerkship patterns
CLERKSHIP_PATTERNS = [
    # "clerked for Judge Richard Posner"
    r"clerked?\s+for\s+(?:Judge\s+|Justice\s+)?([^,.]+?)(?:\s+(?:of|on|at|and)\s|$)",
    # "served as a law clerk to Judge X"
    r"law\s+clerk\s+(?:to|for)\s+(?:Judge\s+|Justice\s+)?([^,.]+?)(?:\s+(?:of|on|at|and|from)\s|$)",
    # "law clerk for Justice X"
    r"clerk\s+for\s+(?:Justice\s+|Judge\s+)?([^,.]+?)(?:\s+(?:of|on|at|and)\s|$)",
    # "served as a clerk for Judge X"
    r"served\s+as\s+a\s+(?:law\s+)?clerk\s+(?:for|to)\s+(?:Judge\s+|Justice\s+)?([^,.]+?)(?:\s+(?:of|on|at|and|from)\s|$)",
]

# Career patterns
CAREER_PATTERNS = [
    # "served as Assistant United States Attorney"
    r"served\s+as\s+(?:an?\s+)?([^,.]+?)(?:\s+(?:from|for|during|in)\s|$)",
    # "worked as a prosecutor"
    r"worked\s+as\s+(?:an?\s+)?([^,.]+?)(?:\s+(?:from|for|during|in)\s|$)",
    # "was in private practice"
    r"was\s+in\s+(private\s+practice|private\s+law)",
    # "served as a judge of the Los Angeles County Superior Court"
    r"served\s+as\s+(?:a\s+)?judge\s+(?:of|on)\s+the\s+([^,.]+)",
    # "partner at [Law Firm]"
    r"partner\s+at\s+([^,.]+)",
    # "professor at [University]"
    r"professor\s+at\s+([^,.]+)",
]

# Notable case patterns
CASE_PATTERNS = [
    r"presided\s+over\s+([^,.]+)",
    r"ruled\s+in\s+([^,.]+)",
    r"wrote\s+(?:the\s+)?(?:majority\s+)?opinion\s+in\s+([^,.]+)",
    r"heard\s+([^,.]+)",
    r"case\s+of\s+([^,.]+)",
]


def extract_education(text):
    """Extract education info from Wikipedia summary text."""
    if not text or pd.isna(text):
        return None, None

    schools = []
    law_schools = []

    # Extract general education
    for pattern in EDU_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            school = m.group(1).strip()
            if school and len(school) > 3 and school not in schools:
                schools.append(school)

    # Extract law schools
    for pattern in LAW_SCHOOL_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            school = m.group(1).strip()
            if school and len(school) > 3 and school not in law_schools:
                law_schools.append(school)

    # Also check if any schools are law schools
    for s in schools:
        if "law" in s.lower() and s not in law_schools:
            law_schools.append(s)

    edu_str = "; ".join(schools) if schools else None
    law_str = "; ".join(law_schools) if law_schools else None

    return edu_str, law_str


def extract_clerkships(text):
    """Extract clerkship info from Wikipedia summary text."""
    if not text or pd.isna(text):
        return None

    clerks = []
    for pattern in CLERKSHIP_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            name = m.group(1).strip()
            # Clean up
            name = re.sub(r'\s+(?:of|on|at|and|from|before|during|for|in)\s+.*$', '', name)
            name = name.strip()
            if name and len(name) > 2 and name not in clerks:
                clerks.append(name)

    return "; ".join(clerks) if clerks else None


def extract_career(text):
    """Extract career info from Wikipedia summary text."""
    if not text or pd.isna(text):
        return None

    positions = []
    for pattern in CAREER_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            pos = m.group(1).strip()
            if pos and len(pos) > 3 and pos not in positions:
                positions.append(pos)

    return "; ".join(positions) if positions else None


def extract_notable_cases(text):
    """Extract notable cases from Wikipedia summary text."""
    if not text or pd.isna(text):
        return None

    cases = []
    for pattern in CASE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            case = m.group(1).strip()
            if case and len(case) > 3 and case not in cases:
                cases.append(case)

    return "; ".join(cases) if cases else None


def extract_birth_date(text):
    """Extract birth date from Wikipedia summary text."""
    if not text or pd.isna(text):
        return None

    # "(born November 12, 1942)"
    m = re.search(r'born\s+(\w+\s+\d+,?\s+\d{4})', text, re.IGNORECASE)
    if m:
        return m.group(1)

    # "(born 1942)"
    m = re.search(r'born\s+(\d{4})', text, re.IGNORECASE)
    if m:
        return m.group(1)

    return None


def extract_appointment_info(text):
    """Extract appointment details from Wikipedia summary text."""
    if not text or pd.isna(text):
        return None

    info = []

    # "appointed by President [Name]"
    m = re.search(r'appointed\s+(?:by|by\s+President)\s+President\s+([A-Z][a-z]+)', text, re.IGNORECASE)
    if not m:
        m = re.search(r'nominated\s+by\s+President\s+([A-Z][a-z]+)', text, re.IGNORECASE)
    if m:
        info.append(f"Appointed by {m.group(1)}")

    # "confirmed by the Senate"
    if "confirmed" in text.lower() and "senate" in text.lower():
        m = re.search(r'confirmed\s+(?:by\s+the\s+)?Senate\s+(?:on\s+)?([^.,]+)', text, re.IGNORECASE)
        if m:
            info.append(f"Confirmed: {m.group(1).strip()}")

    # "since [year]"
    m = re.search(r'(?:since|in)\s+(\d{4})', text, re.IGNORECASE)
    if m:
        info.append(f"Since {m.group(1)}")

    return "; ".join(info) if info else None


def main():
    comp = pd.read_csv("judges_unified_comprehensive.csv")

    # Ensure columns are object type
    for col in ["Wiki_Education", "Wiki_Clerkships", "Wiki_Career", "Education", "Alma mater"]:
        if col not in comp.columns:
            comp[col] = None
        comp[col] = comp[col].astype(object)

    updated = 0
    for idx, row in comp.iterrows():
        text = row.get("Wikipedia Summary", "")
        if pd.isna(text) or str(text).strip() in ("", "nan", "None"):
            continue

        text = str(text)
        changed = False

        # Extract education
        edu, law = extract_education(text)
        if edu:
            comp.at[idx, "Wiki_Education"] = edu
            changed = True
        if law:
            comp.at[idx, "Alma mater"] = law
            changed = True

        # Extract clerkships
        clerks = extract_clerkships(text)
        if clerks:
            comp.at[idx, "Wiki_Clerkships"] = clerks
            changed = True

        # Extract career
        career = extract_career(text)
        if career:
            comp.at[idx, "Wiki_Career"] = career
            changed = True

        # Extract notable cases
        cases = extract_notable_cases(text)
        if cases:
            comp.at[idx, "Notable Cases"] = cases
            changed = True

        # Extract birth date
        bdate = extract_birth_date(text)
        if bdate:
            comp.at[idx, "Birth Date"] = bdate
            changed = True

        if changed:
            updated += 1

    print(f"Updated {updated} judges with extracted info")

    # Coverage
    print("\n=== EXTRACTION COVERAGE ===")
    for col in ["Wiki_Education", "Alma mater", "Wiki_Clerkships", "Wiki_Career", "Notable Cases", "Birth Date"]:
        if col in comp.columns:
            non_null = comp[col].notna() & (comp[col].astype(str).str.strip() != "")
            pct = 100 * non_null.sum() / len(comp)
            print(f"  {col:25s} {non_null.sum():5d}/{len(comp)} ({pct:.1f}%)")

    # Sample
    print("\n=== SAMPLES ===")
    for name in ["Amit Mehta", "Aileen Cannon", "Ada Brown", "Anne Hwang"]:
        row = comp[comp["Judge"] == name]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {name}:")
            for col in ["Wiki_Education", "Alma mater", "Wiki_Clerkships", "Wiki_Career", "Birth Date"]:
                val = r.get(col)
                if pd.notna(val) and str(val).strip() != "":
                    print(f"    {col}: {val}")

    comp.to_csv("judges_unified_comprehensive.csv", index=False)
    print("\nSaved")


if __name__ == "__main__":
    main()