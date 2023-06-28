<script>
	export let name;

	let users = [
		["User", 1, 1.0],
		["User", 1, 0.8],
		["User", 1, 0.5],
		["User", 1, 0.45],
		["User", 1, 0.31],
		["User", 1, 0.11],
		["User", 1, 0.0],
		["User", 1, 0.0],
	];

	let isConnectionLost = false;

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
			users = JSON.parse(message);
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
			{@const percent = Math.round(user[2]*100)}
			{@const isWinner = (user[1]=="F" && user[2]==1.0)}
			
			<tr style="font-size: {1/(index+1)+1}em;" class="rounded-all {isWinner?"winner":""}">
			<td style="text-align: right; padding-right: 1rem; width: 2.5em" class="rounded-left"><b>#{index+1}</b></td>
			<td style="padding-left: 1rem;">{user[0]}</td>
			<td style="text-align: center; width: 1.5em">{user[1]}</td>
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