import Navbar from "../components/dashboard/Navbar";
import Sidebar from "../components/dashboard/Sidebar";
import StatusCard from "../components/dashboard/StatusCard";
import QuickActions from "../components/dashboard/QuickActions";

export default function Dashboard() {
  return (
    <>
      <Navbar />

      <div
        style={{
          display: "flex",
          minHeight: "calc(100vh - 70px)",
        }}
      >
        <Sidebar />

        <main
          style={{
            flex: 1,
            padding: "30px",
          }}
        >
          <h1>AIRES Dashboard</h1>

          <p
            style={{
              marginTop: "10px",
              color: "#94a3b8",
            }}
          >
            AI Intelligent Emergency Response System
          </p>

          <div
            style={{
              display: "flex",
              gap: "20px",
              marginTop: "40px",
              flexWrap: "wrap",
            }}
          >
            <StatusCard title="Active Ambulances" value="1" />
            <StatusCard title="Hospitals Online" value="3" />
            <StatusCard title="Active Emergencies" value="1" />
            <StatusCard title="System Status" value="Online ✅" />
          </div>

          <QuickActions />
        </main>
      </div>
    </>
  );
}