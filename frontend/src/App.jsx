
import React, { useState } from "react";
import axios from "axios";

const BASE_URL = "https://shadowdev.onrender.com"; // Cambia esto si estás en local

export default function App() {
  const [file, setFile] = useState(null);
  const [project, setProject] = useState("");
  const [feature, setFeature] = useState("");
  const [response, setResponse] = useState("");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("secretpassword");

  const getAuthHeaders = () => {
    const token = btoa(`${username}:${password}`);
    return { Authorization: `Basic ${token}` };
  };

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${BASE_URL}/upload`, formData, {
        headers: {
          ...getAuthHeaders(),
          "Content-Type": "multipart/form-data",
        },
      });
      alert(res.data.message || "Uploaded successfully");
      setProject(res.data.project);
    } catch (err) {
      alert("Error uploading file.");
    }
  };

  const handleSuggest = async () => {
    const formData = new FormData();
    formData.append("project", project);
    formData.append("feature", feature);
    try {
      const res = await axios.post(`${BASE_URL}/suggest`, formData, {
        headers: getAuthHeaders(),
      });
      setResponse(res.data.suggestion);
    } catch (err) {
      alert("Error generating suggestion.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-6">Shadow Developer</h1>

      <div className="bg-white p-6 rounded-lg shadow-md w-full max-w-lg">
        <h2 className="text-xl font-semibold mb-2">Login</h2>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-2 border mb-2"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 border mb-4"
        />
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md w-full max-w-lg mt-6">
        <h2 className="text-xl font-semibold mb-2">Upload Project (.zip)</h2>
        <input
          type="file"
          accept=".zip"
          onChange={(e) => setFile(e.target.files[0])}
          className="mb-4"
        />
        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Upload
        </button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md w-full max-w-lg mt-6">
        <h2 className="text-xl font-semibold mb-2">Generate Code</h2>
        <input
          type="text"
          placeholder="Project Name"
          value={project}
          onChange={(e) => setProject(e.target.value)}
          className="w-full p-2 border mb-2"
        />
        <input
          type="text"
          placeholder="Feature to generate"
          value={feature}
          onChange={(e) => setFeature(e.target.value)}
          className="w-full p-2 border mb-4"
        />
        <button
          onClick={handleSuggest}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Suggest Code
        </button>

        {response && (
          <pre className="bg-gray-200 p-4 mt-4 overflow-auto">{response}</pre>
        )}
      </div>
    </div>
  );
}
