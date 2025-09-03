// Simulación de usuarios (esto luego va en la DB)
const users = [
  {
    id: 1,
    email: "admin@ssemi.com",
    password: "$2b$10$mmmpafthxmvDMlilwLnTTOfqHay2L6nQT2ifBZgOQ6BY6pGzydib." // "123456" encriptado
  }
];

export const getUserByEmail = async (email) => {
  return users.find((user) => user.email === email);
};
