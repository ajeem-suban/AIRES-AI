import { Routes, Route } from "react-router-dom";
import RouteDashboard from "./pages/RouteDashboard";
<Route path="/route" element={<RouteDashboard />} />

function App() {
    return (
        <Routes>
            <Route path="/" element={<RouteDashboard />} />
        </Routes>
    );
}

export default App;