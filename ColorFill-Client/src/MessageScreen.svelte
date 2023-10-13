<script lang="ts">
    import { type Scene, type Lobby, GameScene, LobbyScene, SocketWrapper, type Level, MessageScene } from './App';

    export let changeScene: (scene: Scene) => void;
	export let scene: MessageScene;
	export let socket: SocketWrapper

    document.addEventListener("keydown", e=>onKeyPress(e));

    function onKeyPress(e: KeyboardEvent) {
            switch (e.key) {
                case "Enter":
					changeScene(new GameScene(null));
                default:
                    break;
            }
        }

	socket.onLobbyRecieved = function(lobby: Lobby) {
		changeScene(new LobbyScene(lobby));
	}

	socket.onLevelRecieved = function(level: Level) {
		changeScene(new GameScene(level));
	}
</script>

<div class="center-content" style="background: {scene.message.bgFillStyle}">
    <p style="color: {scene.message.fgFillStyle}; font-size: 3em; white-space: pre-line">
		{scene.message.str}
	</p>
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