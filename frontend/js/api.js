// api.js (GLOBAL)

window.API_URL = "https://ssemi.onrender.com";

window.apiFetch = async function (endpoint, method = "GET", data = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json"
    },
    credentials: "include"
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(API_URL + endpoint, options);

  if (!response.ok) {
    let error;
    try {
      error = await response.json();
    } catch {
      error = { detail: "Error de red" };
    }
    throw error;
  }

  return response.json();
};
