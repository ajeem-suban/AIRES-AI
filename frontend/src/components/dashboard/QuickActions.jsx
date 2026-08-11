import { Link } from "react-router-dom";

export default function QuickActions() {
  return (
    <div
      style={{
        display: "flex",
        gap: "15px",
        marginTop: "30px",
      }}
    >
      <Link to="/emergency">🚨 Dispatch</Link>

      <Link to="/tracking">🛰 Tracking</Link>

      <Link to="/hospital">🏥 Hospital</Link>
    </div>
  );
}