<script>
	export let name;

	let users = [
		
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
		};
	}
</script>

<main>
	<h1>{name}</h1>

	<table>
		{#each users as user, index}
			{@const percent = Math.round(user[2]*100)}
			
			<tr style="font-size: {1/(index+1)+1}em;">
			<td style="text-align: right; padding-right: 1em;"><b>#{index+1}</b></td>
			<td style="padding-left: 1em;">{user[0]}</td>
			<td style="text-align: center;">{user[1]}</td>
			<td width="50%">
				<div class="bar" style="width: {percent}%; background: color-mix(in srgb, #c30, #0c0 {percent}%)">
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
		margin: 0 auto;
	}

	tr {
		background: linear-gradient(#444, #333);
	}

	.bar {
		transition: all 0.2s;
		background: #800; 
		padding: 0.5em;
		border-radius: 0 0.5em 0.5em 0;
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
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>