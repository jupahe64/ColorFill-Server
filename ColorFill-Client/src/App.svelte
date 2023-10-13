<script lang="ts">
    import GameScreen from './GameScreen.svelte';
	import LobbyScreen from './LobbyScreen.svelte';
    import { ConnectingScene, GameScene, LobbyScene, MessageScene, SocketWrapper } from './App';
    import type { Scene } from './App';
    import MessageScreen from './MessageScreen.svelte';
    import ConnectingScreen from './ConnectingScreen.svelte';

	if (window.innerWidth>window.innerHeight) {
		window.alert("Landscape orientation is not supported, please rotate your phone and hit refresh");
		throw new Error();
	}

	let socketWrapper: SocketWrapper;
	let currentScene: Scene = new ConnectingScene();
	let hasConnection = false;

	document.addEventListener('gesturestart', function (event) {
        event.preventDefault(); }, false);

	if ("WebSocket" in window) {
		console.log(location);
		let socket = new WebSocket(`ws://${location.hostname}:8000/ws`);
		socketWrapper = new SocketWrapper(socket);

		hasConnection = true;
		
		socketWrapper.onConnectionLost = () => {
			hasConnection = false;
		}
	}
	else {
		alert('Not supported');
	}

	//for testing
	// currentScene = new LobbyScene({players: 
	// 	[
	// 		{name: "Jonas", isReady: true},
	// 		{name: "Sam", isReady: false},
	// 		{name: "Lari", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 		{name: "", isReady: false},
	// 	]
	// });
	// hasConnection = true;

	function changeScene(state: Scene) {
		currentScene = state;
	}
</script>

<main>
	{#if !hasConnection &&  !(currentScene instanceof ConnectingScene)}
		<div class="center-content">
			<p style="font-size: 2em;">Connection Lost</p>
		</div>
	{:else}
		{#key currentScene}
		{#if currentScene instanceof ConnectingScene}
			<ConnectingScreen changeScene={changeScene} socket={socketWrapper}/>
		{:else if currentScene instanceof LobbyScene}
			<LobbyScreen changeScene={changeScene} scene={currentScene} socket={socketWrapper}/>
		{:else if currentScene instanceof GameScene}
			<GameScreen changeScene={changeScene} scene={currentScene} socket={socketWrapper}/>
		{:else if currentScene instanceof MessageScene}
			<MessageScreen changeScene={changeScene} scene={currentScene} socket={socketWrapper}/>
		{/if}
		{/key}
	{/if}
</main>

<style>
	main {
		font-family: Quicksand;
		text-align: center;
		margin: 0;
		overflow: hidden;
		overscroll-behavior: none;

		
		position: absolute;
		inset: 0;
	}

	.center-content {
		display: grid;
		width: 100%;
		height: 100%;
		align-content: center;
		justify-items: stretch;
    	align-items: stretch;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>