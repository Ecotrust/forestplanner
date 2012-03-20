var io = require('socket.io').listen(8001);
var redis = require("redis"),
	client = redis.createClient();

client.subscribe("alert");


io.sockets.on('connection', function(socket) {
	client.on("message", function(channel, message) {
		socket.emit('alert', message);
	});
});
