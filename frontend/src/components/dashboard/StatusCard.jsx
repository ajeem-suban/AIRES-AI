export default function StatusCard({ title, value }) {
  return (
    <div
      style={{
        background: "#1e293b",
        padding: "20px",
        borderRadius: "12px",
        minWidth: "220px",
      }}
    >
      <h4>{title}</h4>

      <h2 style={{ marginTop: "10px" }}>{value}</h2>
    </div>
  );
}