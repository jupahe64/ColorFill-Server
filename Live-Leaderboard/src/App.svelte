<script lang="ts">
	import { Base64Binary } from "./base64-binary";

	export let name: string;

	class UserInfo {
		constructor(
			public name: string,
			public levelID: number | string,
			public progress: number,
			public solidBlockSvgPath: string,
			public filledBlockSvgPath: string,
			public levelSvgWidth: number,
			public levelSvgHeight: number
		) {}
	}

	let users: UserInfo[] = [
		new UserInfo("User", 1, 1.0, "", "", 1, 1),
		new UserInfo("User", 1, 0.8, "", "", 1, 1),
		new UserInfo("User", 1, 0.5, "", "", 1, 1),
		new UserInfo("User", 1, 0.45, "", "", 1, 1),
		new UserInfo("User", 1, 0.31, "", "", 1, 1),
		new UserInfo("User", 1, 0.11, "", "", 1, 1),
		new UserInfo("User", 1, 0.0, "", "", 1, 1),
		new UserInfo("User", 1, 0.0, "", "", 1, 1),
	];

	let isConnectionLost = false;

	class LevelProgressCacheEntry {
		constructor(
			public progress: number,
			public solidBlockSvgPath: string, 
			public filledBlockSvgPath: string,
			public levelSvgWidth: number,
			public levelSvgHeight: number
			) { }
	}

	let progressMessageCache: Map<string, LevelProgressCacheEntry> = new Map();

	if ("WebSocket" in window) {
		console.log(location);
		let socket = new WebSocket(`ws://${location.hostname}:8000/leaderboard/ws`);
		
		socket.onopen = function() {
			console.log("WebSocket connection established.");
		};

		socket.onmessage = function(event) {
			/**@type {String} */
			const message = event.data;
			console.log("Received message: " + message);
			let incomingUsers: Object[][] = JSON.parse(message);

			var newUsers: UserInfo[] = [];

			for (const user of incomingUsers) {
				let name = (user[0] as string);
				let levelID = (user[1] as number);
				let levelProgress = (user[2] as number);
				let progressMessage = (user[3] as string);
				let cacheEntry = progressMessageCache.get(progressMessage);

				if (!cacheEntry) {
					let values = progressMessage.split(";");
					let gridSizeX = parseInt(values[0]);
					let gridSizeY = parseInt(values[1]);
					let levelString = values[2];
					let levelBytes = Base64Binary.decode(levelString);

					let solidBlockSvgPath = "";
					let filledBlockSvgPath = "";

					let emptyCount = 0;
					let filledCount = 0;
					
					for (let i = 0; i < levelBytes.length; i++) {
						for (let j = 0; j < 4; j++) {
							const block = (levelBytes[i] >> j*2) & 0b11;
							
							const x = (i*4+j) % gridSizeX;
							const y = Math.trunc((i*4+j) / gridSizeX);

							switch (block) {
								case 0:
									emptyCount++;
									break;
								case 1:
									solidBlockSvgPath += `M${x} ${y}h1v1h-1`;
									break;
								case 2:
									filledBlockSvgPath += `M${x} ${y}h1v1h-1`;
									filledCount++;
									break;
							}
						}
					}

					cacheEntry = new LevelProgressCacheEntry(levelProgress, solidBlockSvgPath, filledBlockSvgPath,
															 gridSizeX, gridSizeY);

					progressMessageCache[progressMessage] = cacheEntry;
				}

				newUsers.push(new UserInfo(
					name,
					levelID,
					cacheEntry.progress,
					cacheEntry.solidBlockSvgPath,
					cacheEntry.filledBlockSvgPath,
					cacheEntry.levelSvgWidth,
					cacheEntry.levelSvgHeight
				))
			}


			users = newUsers;
		};

		socket.onerror = function(error) {
			console.error("WebSocket error: " + error);
			// logger.innerHTML += "WebSocket error: " + JSON. stringify(error) + "<br/>";
		};

		socket.onclose = function(event) {
			console.log("WebSocket connection closed with code: " + event.code);
			isConnectionLost = true;

			setInterval(function () {location.reload()}, 1000);
		};
	}
</script>

<main>
	<h1>{name}</h1>

	<table>
		{#each users as user, index}
			{@const percent = Math.round(user.progress*100)}
			{@const isWinner = (user.levelID=="F" && user.progress==1.0)}
			
			<tr style="font-size: {1/(index+1)+1}em;" class="rounded-all {isWinner?"winner":""}">
			<td style="text-align: right; padding-right: 1rem; width: 2.5em" class="rounded-left"><b>#{index+1}</b></td>
			<td style="padding-left: 1rem;">{user.name}</td>
			<td style="text-align: center; width: 1.5em">{user.levelID}</td>
			<td style="text-align: center; width: 1.5em">
				<svg width="100%" viewBox="0 0 {user.levelSvgWidth} {user.levelSvgHeight}">
					<path fill="#fff" d="{user.filledBlockSvgPath}"/>
					<rect stroke-width="0.5" stroke="#fff" fill="transparent" x="0" y="0" width="{user.levelSvgWidth}" height="{user.levelSvgHeight}" />
				</svg>
			</td>
			<td width="50%" class="rounded-right">
				<div class="bar rounded-right" style="width: calc({percent}% - 1em); background: color-mix(in srgb, #c30, #0c0 {percent}%)">
					{percent}%
				</div>
			</td>
			</tr>
		{/each}
	</table>

	{#if isConnectionLost}
		<p>Connection Lost</p>
	{/if}
</main>

<style>
	main {
		font-family: Quicksand;
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 10%;
	}

	tr {
		background: linear-gradient(#444, #333);
	}

	.rounded-left {
		border-radius: 0.5em 0 0 0.5em;
	}

	.rounded-right {
		border-radius: 0 0.5em 0.5em 0;
	}

	.rounded-all {
		border-radius: 0.5em;
	}

	.bar {
		transition: all 0.2s;
		background: #800; 
		padding: 0.5em;
		border-radius: 0 0.5em 0.5em 0;
	}

	.winner {
		transition: outline-width 1.5s;
		outline: 3px solid #ff3;
		-webkit-box-shadow: 0px 0px 48px -1px rgba(251,255,60,0.47); 
box-shadow: 0px 0px 18px 0px rgba(251,255,60,0.47);
	}

	h1 {
		color: #ff3e00;
		text-transform: uppercase;
		font-size: 4em;
		font-weight: 100;
	}

	table {
		font-size: large;
		text-align: left;
		width: 100%;

		border-collapse: separate;
  		border-spacing: 0 0.2rem;
	}

	td {
		outline: 2px solid #0002;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>