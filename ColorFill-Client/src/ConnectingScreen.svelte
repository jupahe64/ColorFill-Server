<script lang="ts">
    import { type Scene, type Lobby, GameScene, LobbyScene, SocketWrapper, type Level, MessageScene, type Message } from './App';
    import { calculateLevelSizeRatio } from './Game';

    export let changeScene: (scene: Scene) => void;
	export let socket: SocketWrapper

    socket.onLobbyRecieved = function(lobby: Lobby) {
		changeScene(new LobbyScene(lobby));
	}

	socket.onLevelRecieved = function(level: Level) {
		changeScene(new GameScene(level));
	}

	socket.onMessageRecieved = function(message: Message) {
		changeScene(new MessageScene(message));
	}

	if (socket.isOpen())
		socket.sendRegisterPlayer(localStorage.getItem("playerName"), 
				calculateLevelSizeRatio({width: window.innerWidth, height: window.innerHeight}));
	else
		socket.onConnectionEstablished = function(){
			socket.sendRegisterPlayer(localStorage.getItem("playerName"), 
				calculateLevelSizeRatio({width: window.innerWidth, height: window.innerHeight}));
		};
</script>

<div class="center-content">
	<p style="font-size: 2em;">Connecting</p>
</div>

<style>
	.center-content {
		display: grid;
		width: 100%;
		height: 100%;
		align-content: center;
		justify-items: stretch;
    	align-items: stretch;
	}
</style>