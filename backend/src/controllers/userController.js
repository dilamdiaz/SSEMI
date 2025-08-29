// controllers/userController.js
exports.getUsers = (req, res) => {
  res.json([{ id: 1, name: "Dilam" }, { id: 2, name: "Samuel" }]);
};
