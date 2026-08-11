import { useEffect, useState } from "react";

import { getRecommendedHospital } from "../services/hospital";

export default function HospitalDashboard() {
  const [hospital, setHospital] = useState(null);

  useEffect(() => {
    async function loadHospital() {
      try {
        const data = await getRecommendedHospital();
        setHospital(data);
      } catch (error) {
        console.error(error);
      }
    }

    loadHospital();
  }, []);

  if (!hospital)
    return <h2 style={{ padding: "20px" }}>Loading...</h2>;

  return (
    <div style={{ padding: "30px" }}>
      <h1>🏥 Hospital Dashboard</h1>

      <br />

      <h2>{hospital.hospital.name}</h2>

      <p>
        <strong>Distance:</strong> {hospital.distance_km} km
      </p>

      <p>
        <strong>ETA:</strong> {hospital.estimated_time}
      </p>

      <p>
        <strong>Score:</strong> {hospital.score}
      </p>

      <p>
        <strong>Reason:</strong> {hospital.reason}
      </p>

      <br />

      <h3>Facilities</h3>

      <p>
        ICU :
        {hospital.hospital.icu_available ? " ✅ Yes" : " ❌ No"}
      </p>

      <p>
        Beds :
        {hospital.hospital.beds_available}
      </p>

      <p>
        Specialties :
        {hospital.hospital.specialties.join(", ")}
      </p>
    </div>
  );
}