import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import VoiceWidget from "./components/VoiceWidget";
import AdminDashboard from "./components/AdminDashboard";

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <header className="bg-white shadow-sm p-4 border-b">
          <h1 className="text-xl font-bold text-center">
            Restaurant AI Booking
          </h1>
        </header>
        <main className="flex-1 p-4 md:p-8 flex justify-center items-start">
          <Routes>
            <Route path="/" element={<VoiceWidget />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
