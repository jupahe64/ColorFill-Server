<script lang="ts">
    import { fade } from 'svelte/transition';
    import { type Scene, type Lobby, GameScene, LobbyScene, SocketWrapper, type Level } from './App';
    import { calculateLevelSizeRatio } from './Game';

    export let changeScene: (scene: Scene) => void;
	export let scene: LobbyScene;
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

	let playersReady = scene.lobby.players;

	let playerName = localStorage.getItem("playerName");
    $: {
		localStorage.setItem("playerName", playerName);
		socket.sendRegisterPlayer_nameOnly(playerName);
	}

	socket.onLobbyRecieved = function(lobby: Lobby) {
		playersReady = lobby.players;
	}

	socket.onLevelRecieved = function(level: Level) {
		changeScene(new GameScene(level));
	}

	let isReady = false;
</script>

<div class="center-content" style="grid-template-rows: 2fr 1fr 2fr;">
    <div class="center-content" style="grid-template-rows: 1fr auto;">
        <h1 style="font-size: 3em; opacity: 50%">Lobby</h1>
        {#if !isReady}
		<input type="text" id="player_name" bind:value={playerName} style="height: 2em; margin: 0 2em"/>
        {/if}
    </div>
    {#if !isReady}
    <button disabled = {playerName==""} 
		on:click={(e) => {isReady = true; socket.sendAnnounceReady()}} 
		type="button" class="ready-button">
			{playersReady.length==0?"Play alone":"Ready!"}
	</button>
    {:else}
    <p in:fade={{duration: 2000}} style="font-size: 2em;">Waiting</p>
    {/if}
    <div style="overflow: scroll;">
    {#if playersReady.length==0}
        <p style="opacity: 0.8; font-size: 1.5em; ">No other players</p>
    {:else}
        {#each playersReady as entry}
            <p>
				{#if entry.name == ""}
                <i style="opacity: 0.5;">Unknown</i>
				{:else}
				<i>{entry.name}</i>
				{/if}

                {#if entry.isReady}
                <span style="color: #0f0;">ready</span>
                {:else}
                <span style="color: #999;">pending</span>
                {/if}
                
        {/each}
    {/if}
    </div>
</div>

<style>
	.ready-button {
		margin: 1em;
		padding: 0.5em;
		font-size: 2.5em;
		color: #c2ffc2;
		background-color: #3b693b;
		border: #78c478 solid 0.15em;
	}

	.ready-button:active:enabled {
		transition: 0.4s;
		background-color: #78c478;
	}

    .center-content {
		display: grid;
		width: 100%;
		height: 100%;
		align-content: center;
		justify-items: stretch;
    	align-items: stretch;
	}

    button {
		border-radius: 1em;
		border: none;
	}

	button:disabled {
		opacity: 50%;
	}

	input {
		background: none;
		border: #555 solid 2px;
		border-radius: 0.4em;
		color: #ccc;
	}

	input:focus {
		background: none;
		border: #888 solid 2px;
		border-radius: 0.4em;
		color: #ccc;
		outline: none;
	}
</style>