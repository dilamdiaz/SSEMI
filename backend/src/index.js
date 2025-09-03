import express from "express";
import dotenv from "dotenv";
import loginRoutes from "./routes/loginRoutes.js";

dotenv.config();

const app = express();
app.use(express.json());

// ruta de prueba para verificar que el servidor responde
app.get("/", (req, res) => {
  res.send("API SSEMI funcionando 🚀");
});

// rutas reales
app.use("/login", loginRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});


import { verifyToken } from "./middlewares/loginMiddleware.js";

// ruta protegida de prueba
app.get("/protected", verifyToken, (req, res) => {
  res.json({
    message: "Accediste a la ruta protegida ✅",
    user: req.user, // esto viene del token decodificado
  });
});
