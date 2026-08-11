import { Link } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside
      style={{
        width: "250px",
        background: "#111827",
        padding: "20px",
      }}
    >
      <h3>Navigation</h3>

      <nav
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "15px",
          marginTop: "20px",
        }}
      >
        <Link to="/">Dashboard</Link>
        <Link to="/emergency">Emergency</Link>
        <Link to="/tracking">Tracking</Link>
        <Link to="/hospital">Hospital</Link>
      </nav>
    </aside>
  );
}