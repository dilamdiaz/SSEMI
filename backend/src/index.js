const express = require("express");
const userRoutes = require("./routes/userRoutes");

const app = express();

app.use(express.json()); // para leer JSON en body

app.use("/users", userRoutes);

app.listen(3000, () => {
  console.log("Servidor corriendo en http://localhost:3000");
});
