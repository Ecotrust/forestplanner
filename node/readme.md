# socket bouncer
## installation

	sudo apt-get install node redis-server curl
	curl http://npmjs.org/install.sh | sh
	npm install
	node server.js

## usage
Reload the page and then publish an alert using the redis command line tool.

	redis-cli
	redis 127.0.0.1:6379> publish alert "Your report is complete."

You should see an alert window appear in the browser with the text displayed.


