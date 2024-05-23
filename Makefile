
all: atom router algo tool
	@echo "Done!"
	pm2 status
atom:
	pm2 start ./daemon/atom.sh --name atom --silent --log

router:
	pm2 start ./daemon/ranger_fox.sh --name ranger_fox --silent --log
	pm2 start ./daemon/ranger_claw.sh --name ranger_claw --silent --log

algo:
	pm2 start ./daemon/algo_chat.sh --name algo_chat --silent --log
	pm2 start ./daemon/algo_turn.sh --name algo_turn --silent --log

tool:
	pm2 start ./daemon/runtime_email.sh --name run_email --silent --log
	pm2 start ./daemon/runtime_wechat.sh --name run_wechat --silent --log

clean:
	pm2 delete all
