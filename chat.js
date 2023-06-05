const express = require('express');
const app = express();
const http = require('http');
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/templates/chat_index.html');
});


app.get("/msg/:msg", (req, res) => {
  const msg = req.params.msg;
  io.emit("chat message", msg);
  res.end();
});

io.on('connection', (socket) => {
  socket.on('chat message', (msg) => {
    io.emit('chat message', msg);
  });
});


server.listen(8008, () => {
  console.log('listening on *:8008');
});
