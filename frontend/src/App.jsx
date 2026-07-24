import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminPage from "./pages/AdminPage";
import BookDetailPage from "./pages/BookDetailPage";
import LibraryPage from "./pages/LibraryPage";
import LoginPage from "./pages/LoginPage";
import SettingsPage from "./pages/SettingsPage";
import UploadPage from "./pages/UploadPage";

function Protected({ children, adminOnly }) {
  return (
    <ProtectedRoute adminOnly={adminOnly}>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Protected><LibraryPage /></Protected>} />
      <Route path="/books/:bookId" element={<Protected><BookDetailPage /></Protected>} />
      <Route path="/upload" element={<Protected><UploadPage /></Protected>} />
      <Route path="/settings" element={<Protected><SettingsPage /></Protected>} />
      <Route path="/admin" element={<Protected adminOnly><AdminPage /></Protected>} />
    </Routes>
  );
}
