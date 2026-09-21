import json
from pathlib import Path

from app.models.hospital import Hospital
from app.utils.distance import calculate_distance

DATA_FILE = Path(__file__).parent.parent / "data" / "hospitals.json"


def recommend_hospital(patient_lat: float, patient_lon: float, emergency_type: str):

    try:
        with open(DATA_FILE, "r") as f:
            hospitals = json.load(f)

        hospital_list = [Hospital(**hospital) for hospital in hospitals]

        if len(hospital_list) == 0:
            return {
                "error": "No hospitals found."
            }

        best_hospital = None
        best_score = float("-inf")

        # Only consider hospitals that can actually take this patient:
        # a free bed AND a matching specialty (case-insensitive).
        wanted = emergency_type.strip().lower()
        candidates = [
            h for h in hospital_list
            if h.beds_available > 0
            and wanted in [s.lower() for s in h.specialties]
        ]
        # Fallback 1: general emergency hospitals with a free bed
        if not candidates:
            candidates = [
                h for h in hospital_list
                if h.beds_available > 0
                and "emergency" in [s.lower() for s in h.specialties]
            ]
        # Fallback 2: any hospital with a free bed
        if not candidates:
            candidates = [h for h in hospital_list if h.beds_available > 0]
        if not candidates:
            return {"error": "No hospital has a free bed."}

        for hospital in candidates:

            distance = calculate_distance(
                patient_lat,
                patient_lon,
                hospital.latitude,
                hospital.longitude,
            )

            score = 0

            # Beds
            score += min(hospital.beds_available, 10) * 2  # cap: big hospitals must not win on beds alone

            # ICU
            if hospital.icu_available:
                score += 40

            # Specialty
            if emergency_type in hospital.specialties:
                score += 60
            elif "Emergency" in hospital.specialties:
                score += 20

            # Distance penalty
            score -= distance * 111 * 5  # 5 points per km (degrees -> km)

            print(f"{hospital.name} -> Score: {score}")

            if best_hospital is None or score > best_score:
                best_hospital = hospital
                best_score = score

        if best_hospital is None:
            return {
                "error": "Unable to recommend a hospital."
            }

        return {
            "hospital": best_hospital.name,
            "distance_km": round(
                calculate_distance(
                    patient_lat,
                    patient_lon,
                    best_hospital.latitude,
                    best_hospital.longitude,
                ) * 111,
                2,
            ),
            "score": round(best_score, 2),
            "beds": best_hospital.beds_available,
            "icu": best_hospital.icu_available,
            "specialties": best_hospital.specialties,
        }

    except Exception as e:
        return {
            "error": str(e)
        }