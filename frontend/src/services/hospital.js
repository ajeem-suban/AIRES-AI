import api from "./api";

export async function getRecommendedHospital() {
  const response = await api.post("/hospital/recommend", {
    patient_latitude: 10.955,
    patient_longitude: 78.620,
    emergency_type: "Cardiology",
  });

  return response.data;
}