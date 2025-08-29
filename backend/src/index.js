import express from "express";

const express = require("express");
const app = express();

app.use(express.json()); // para leer JSON en body

const userRoutes = require("./routes/userRoutes");
app.use("/users", userRoutes);

app.listen(3000, () => {
  console.log("Servidor corriendo en http://localhost:3000");
});
