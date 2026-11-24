"""
Map district-level caseload data to individual judges.

Attaches per-district caseload metrics (filings, cases per judgeship, median
disposition times, case type breakdown) to each judge based on their court.

Also computes the top case types for each district.
"""

import pandas as pd
import json
import re

NATURE_LABELS = {
    "A": "Social Security", "B": "Personal Injury/Product Liability",
    "C": "Prisoner Petitions", "D": "Forfeitures and Penalties",
    "E": "Real Property", "F": "Labor Suits", "G": "Contracts",
    "H": "Torts (other)", "I": "Intellectual Property",
    "J": "Civil Rights", "K": "Immigration", "L": "Other Statutes",
}

CRIMINAL_LABELS = {
    "A": "Marijuana", "B": "All Other Drugs", "C": "Immigration",
    "D": "Firearms and Explosives", "E": "Fraud", "F": "Violent Offenses",
    "G": "Sex Offenses", "H": "Forgery and Counterfeiting", "I": "Other",
    "J": "Regulatory", "K": "Prohibition", "L": "Other",
}


def map_district_to_court(name):
    """Map district name from PDF to court abbreviation."""
    if not name:
        return None

    mappings = {
        "DISTRICT OF COLUMBIA": "D.D.C.",
        "MAINE": "D. Me.", "MASSACHUSETTS": "D. Mass.",
        "NEW HAMPSHIRE": "D.N.H.", "RHODE ISLAND": "D.R.I.",
        "PUERTO RICO": "D.P.R.", "CONNECTICUT": "D. Conn.",
        "NEW YORK NORTHERN": "N.D.N.Y.", "NEW YORK EASTERN": "E.D.N.Y.",
        "NEW YORK SOUTHERN": "S.D.N.Y.", "NEW YORK WESTERN": "W.D.N.Y.",
        "DELAWARE": "D. Del.", "NEW JERSEY": "D.N.J.",
        "PENNSYLVANIA EASTERN": "E.D. Pa.", "PENNSYLVANIA MIDDLE": "M.D. Pa.",
        "PENNSYLVANIA WESTERN": "W.D. Pa.", "VIRGIN ISLANDS": "D.V.I.",
        "MARYLAND": "D. Md.",
        "VIRGINIA EASTERN": "E.D. Va.", "VIRGINIA WESTERN": "W.D. Va.",
        "WEST VIRGINIA NORTHERN": "N.D. W. Va.", "WEST VIRGINIA SOUTHERN": "S.D. W. Va.",
        "NORTH CAROLINA EASTERN": "E.D.N.C.", "NORTH CAROLINA MIDDLE": "M.D.N.C.",
        "NORTH CAROLINA WESTERN": "W.D.N.C.", "SOUTH CAROLINA": "D.S.C.",
        "GEORGIA NORTHERN": "N.D. Ga.", "GEORGIA MIDDLE": "M.D. Ga.",
        "GEORGIA SOUTHERN": "S.D. Ga.",
        "FLORIDA NORTHERN": "N.D. Fla.", "FLORIDA MIDDLE": "M.D. Fla.",
        "FLORIDA SOUTHERN": "S.D. Fla.",
        "ALABAMA NORTHERN": "N.D. Ala.", "ALABAMA MIDDLE": "M.D. Ala.",
        "ALABAMA SOUTHERN": "S.D. Ala.",
        "MISSISSIPPI NORTHERN": "N.D. Miss.", "MISSISSIPPI SOUTHERN": "S.D. Miss.",
        "LOUISIANA EASTERN": "E.D. La.", "LOUISIANA MIDDLE": "M.D. La.",
        "LOUISIANA WESTERN": "W.D. La.",
        "TEXAS NORTHERN": "N.D. Tex.", "TEXAS SOUTHERN": "S.D. Tex.",
        "TEXAS EASTERN": "E.D. Tex.", "TEXAS WESTERN": "W.D. Tex.",
        "ARKANSAS EASTERN": "E.D. Ark.", "ARKANSAS WESTERN": "W.D. Ark.",
        "MISSOURI EASTERN": "E.D. Mo.", "MISSOURI WESTERN": "W.D. Mo.",
        "IOWA NORTHERN": "N.D. Iowa", "IOWA SOUTHERN": "S.D. Iowa",
        "MINNESOTA": "D. Minn.", "NEBRASKA": "D. Neb.",
        "NORTH DAKOTA": "D.N.D.", "SOUTH DAKOTA": "D.S.D.",
        "MONTANA": "D. Mont.", "IDAHO": "D. Idaho",
        "NEVADA": "D. Nev.", "ARIZONA": "D. Ariz.",
        "ALASKA": "D. Alaska", "HAWAII": "D. Haw.", "OREGON": "D. Or.",
        "WASHINGTON EASTERN": "E.D. Wash.", "WASHINGTON WESTERN": "W.D. Wash.",
        "GUAM": "D. Guam", "NORTHERN MARIANA ISLANDS": "D. N. Mar. I.",
        "CALIFORNIA NORTHERN": "N.D. Cal.", "CALIFORNIA EASTERN": "E.D. Cal.",
        "CALIFORNIA CENTRAL": "C.D. Cal.", "CALIFORNIA SOUTHERN": "S.D. Cal.",
        "COLORADO": "D. Colo.", "KANSAS": "D. Kan.",
        "NEW MEXICO": "D.N.M.",
        "OKLAHOMA EASTERN": "E.D. Okla.", "OKLAHOMA NORTHERN": "N.D. Okla.",
        "OKLAHOMA WESTERN": "W.D. Okla.",
        "UTAH": "D. Utah", "WYOMING": "D. Wyo.",
        "KENTUCKY EASTERN": "E.D. Ky.", "KENTUCKY WESTERN": "W.D. Ky.",
        "TENNESSEE EASTERN": "E.D. Tenn.", "TENNESSEE MIDDLE": "M.D. Tenn.",
        "TENNESSEE WESTERN": "W.D. Tenn.",
        "OHIO NORTHERN": "N.D. Ohio", "OHIO SOUTHERN": "S.D. Ohio",
        "MICHIGAN EASTERN": "E.D. Mich.", "MICHIGAN WESTERN": "W.D. Mich.",
        "ILLINOIS NORTHERN": "N.D. Ill.", "ILLINOIS SOUTHERN": "S.D. Ill.",
        "ILLINOIS CENTRAL": "C.D. Ill.",
        "INDIANA NORTHERN": "N.D. Ind.", "INDIANA SOUTHERN": "S.D. Ind.",
        "WISCONSIN EASTERN": "E.D. Wis.", "WISCONSIN WESTERN": "W.D. Wis.",
    }

    name_upper = name.upper().strip()
    return mappings.get(name_upper, name_upper)


def get_top_case_types(civil_types, criminal_types, n=3):
    """Get the top N civil and criminal case types by volume."""
    result = {}

    if civil_types:
        sorted_civil = sorted(civil_types.items(), key=lambda x: x[1] or 0, reverse=True)
        result["top_civil_types"] = "; ".join(
            f"{NATURE_LABELS.get(k, k)} ({v:,})" for k, v in sorted_civil[:n] if v and v > 0
        )

    if criminal_types:
        sorted_criminal = sorted(criminal_types.items(), key=lambda x: x[1] or 0, reverse=True)
        result["top_criminal_types"] = "; ".join(
            f"{CRIMINAL_LABELS.get(k, k)} ({v:,})" for k, v in sorted_criminal[:n] if v and v > 0
        )

    return result


def main():
    comp = pd.read_csv("judges_unified_comprehensive.csv")

    with open("district_caseload.json") as f:
        districts = json.load(f)

    # Build lookup by court abbreviation
    caseload_by_court = {}
    for d in districts:
        court = map_district_to_court(d["district"])
        if court:
            # Compute top case types
            top = get_top_case_types(d.get("civil_types"), d.get("criminal_types"))
            d.update(top)
            caseload_by_court[court] = d

    print(f"Mapped {len(caseload_by_court)} districts to courts")

    # Add caseload columns to the unified CSV
    new_cols = [
        "District Filings", "Civil Cases per Judgeship", "Weighted Filings per Judgeship",
        "Median Civil Disposition (months)", "Judgeships", "Vacant Judgeship Months",
        "Criminal Cases per Judgeship", "Trials Completed", "Civil Cases Over 3 Years Old (%)",
        "District Civil Filings", "District Criminal Filings", "Top Civil Case Types", "Top Criminal Case Types",
    ]
    for col in new_cols:
        comp[col] = None

    updated = 0
    for idx, row in comp.iterrows():
        court = row.get("Court", "")
        if pd.isna(court) or str(court).strip() in ("", "nan", "None"):
            continue

        court = str(court).strip()
        if court in caseload_by_court:
            d = caseload_by_court[court]
            comp.at[idx, "District Filings"] = d.get("filings_total")
            comp.at[idx, "Civil Cases per Judgeship"] = d.get("civil_per_judgeship")
            comp.at[idx, "Weighted Filings per Judgeship"] = d.get("weighted_filings")
            comp.at[idx, "Median Civil Disposition (months)"] = d.get("median_civil_months")
            comp.at[idx, "Judgeships"] = d.get("judgeships")
            comp.at[idx, "Vacant Judgeship Months"] = d.get("vacant_months")
            comp.at[idx, "Criminal Cases per Judgeship"] = d.get("criminal_per_judgeship")
            comp.at[idx, "Trials Completed"] = d.get("trials_completed")
            comp.at[idx, "Civil Cases Over 3 Years Old (%)"] = d.get("civil_over_3_years")
            comp.at[idx, "District Civil Filings"] = d.get("civil_total")
            comp.at[idx, "District Criminal Filings"] = d.get("criminal_total")
            comp.at[idx, "Top Civil Case Types"] = d.get("top_civil_types")
            comp.at[idx, "Top Criminal Case Types"] = d.get("top_criminal_types")
            updated += 1

    print(f"Updated {updated} judges with caseload data")

    # Coverage
    print("\n=== CASELOAD COVERAGE ===")
    for col in new_cols:
        if col in comp.columns:
            non_null = comp[col].notna() & (comp[col].astype(str).str.strip() != "")
            pct = 100 * non_null.sum() / len(comp)
            print(f"  {col:40s} {non_null.sum():5d}/{len(comp)} ({pct:.1f}%)")

    # Samples
    print("\n=== SAMPLES ===")
    for name in ["Amit Mehta", "Aileen Cannon", "A. Joe Fish", "Anne Hwang"]:
        row = comp[comp["Judge"] == name]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {name}:")
            for col in new_cols:
                val = r.get(col)
                if pd.notna(val) and str(val).strip() not in ("", "nan", "None"):
                    print(f"    {col}: {val}")

    comp.to_csv("judges_unified_comprehensive.csv", index=False)
    print("\nSaved judges_unified_comprehensive.csv")


if __name__ == "__main__":
    main()