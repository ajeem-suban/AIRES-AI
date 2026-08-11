import { useEffect, useState } from "react";

export default function RouteDashboard() {
    const [route, setRoute] = useState(null);

    useEffect(() => {
        const socket = new WebSocket(
            "ws://localhost:8000/ws/routing/AMB001"
        );

        socket.onmessage = (event) => {
            setRoute(JSON.parse(event.data));
        };

        socket.onerror = (error) => {
            console.error("WebSocket Error:", error);
        };

        return () => socket.close();
    }, []);

    if (!route) {
        return (
            <div style={{ padding: "40px" }}>
                <h2>🚑 Connecting to AIRES...</h2>
            </div>
        );
    }

    const getTrafficColor = () => {
        switch (route.traffic_status) {
            case "Light":
                return "#22c55e"; // Green
            case "Moderate":
                return "#f59e0b"; // Orange
            case "Heavy":
                return "#ef4444"; // Red
            default:
                return "#6b7280";
        }
    };

    return (
        <div
            style={{
                padding: "30px",
                fontFamily: "Arial, sans-serif",
                background: "#111827",
                minHeight: "100vh",
                color: "white",
            }}
        >
            <h1>🚑 AIRES Dynamic Routing Dashboard</h1>

            <hr />

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3,1fr)",
                    gap: "20px",
                    marginTop: "20px",
                }}
            >
                <div
                    style={{
                        background: "#1f2937",
                        padding: "20px",
                        borderRadius: "10px",
                    }}
                >
                    <h3>🚦 Traffic</h3>

                    <p
                        style={{
                            color: getTrafficColor(),
                            fontWeight: "bold",
                            fontSize: "20px",
                        }}
                    >
                        {route.traffic_status}
                    </p>
                </div>

                <div
                    style={{
                        background: "#1f2937",
                        padding: "20px",
                        borderRadius: "10px",
                    }}
                >
                    <h3>🛣 Route</h3>

                    <p>{route.recommended_route}</p>
                </div>

                <div
    style={{
        background: "#1f2937",
        padding: 20,
        marginTop: 20,
        borderRadius: 10
    }}
>
    <h3>🤖 AI Road Analysis</h3>

    <p>
        <strong>Detected Event:</strong> {route.road_event}
    </p>

    <p>
        {route.event_description}
    </p>
</div>
            </div>

            <div
                style={{
                    marginTop: "25px",
                    background: "#1f2937",
                    padding: "20px",
                    borderRadius: "10px",
                }}
            >
                <h3>📍 Current Route</h3>

                <p>
                    <strong>Current:</strong> {route.current_route}
                </p>

                <p>
                    <strong>Recommended:</strong> {route.recommended_route}
                </p>

                <p>
                    <strong>Time Saved:</strong> {route.time_saved} Minutes
                </p>
            </div>

            {route.rerouted && (
                <div
                    style={{
                        background:
                            route.traffic_status === "Heavy"
                                ? "#7f1d1d"
                                : "#78350f",
                        border: "2px solid #f59e0b",
                        padding: "20px",
                        marginTop: "25px",
                        borderRadius: "10px",
                    }}
                >
                    <h2>🚨 AI Decision</h2>

<p>
    <strong>{route.road_event}</strong> detected.
</p>

<p>
    {route.event_description}
</p>

<p>
    Switching ambulance to
    <strong> {route.recommended_route}</strong>
</p>

<p>
    ETA Improved by
    <strong> {route.time_saved} minutes</strong>
</p>
                </div>
            )}
        </div>
    );
}