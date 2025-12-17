// api.js (GLOBAL)

window.API_URL = "https://ssemi.onrender.com";

window.apiFetch = async function (endpoint, method = "GET", data = null) {
  const token = localStorage.getItem("ssemi_token");

  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const options = {
    method,
    headers,
    credentials: "include"
  };

  if (data !== null && data !== undefined) {
    options.body = JSON.stringify(data);
  }

  const url = endpoint.startsWith("http") ? endpoint : (API_URL + endpoint);

  const response = await fetch(url, options);

  let parsed = null;
  try { parsed = await response.json(); } catch { parsed = null; }

  if (!response.ok) {
    throw parsed || { detail: `HTTP ${response.status}` };
  }

  return parsed;
};

