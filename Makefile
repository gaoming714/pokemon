all: server ranger algo tool
	@echo "Done!"

server:
	pm2 start daemon.atom.sh --name atom --silent --log
ranger:
	pm2 start daemon.ranger_fox.sh --name fox --silent --log
	pm2 start daemon.ranger_claw.sh --name claw --silent --log
algo:
	pm2 start daemon.runtime_chat.sh --name chat --silent --log
	pm2 start daemon.runtime_turn.sh --name turn --silent --log
tool:
	pm2 start daemon.runtime_email.sh --name email --silent --log
	pm2 start daemon.runtime_wechat.sh --name wechat --silent --log