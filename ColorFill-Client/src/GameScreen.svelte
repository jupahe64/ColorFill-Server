<script lang="ts">
	import { onMount } from 'svelte';
    import { GameScene, type Scene, type SocketWrapper, type Message, MessageScene, type Level, type OverlayMessage } from './App';
    import { BlockTypes, PlayingField, Rectangle, calculatePreferredResetBtnHeight } from './Game';
	const BLOCK_SIZE = 30;


	let canvas: HTMLCanvasElement;
	let overlay: HTMLDivElement;
	let overlayText: string;
	let overlayFgStyle: string;

    export let changeScene: (scene: Scene) => void;
    export let scene: GameScene;
	export let socket: SocketWrapper

	socket.onLevelRecieved = function(level: Level) {
		changeScene(new GameScene(level));
	}

	socket.onMessageRecieved = function(message: Message) {
		changeScene(new MessageScene(message));
	}

	function getLevelSizeFactor() {
		return canvas.clientWidth / (scene.level.width * BLOCK_SIZE);
	}

	const animations = {
		"none": [
			{ transform: 'none', opacity: '100%' },
			{ transform: 'none', opacity: '0%' },
		],
		"fly-in": [
			{ transform: 'translateY(-80%)', opacity: '100%', easing: 'ease-out' },
			{ transform: 'translateY(0%)', opacity: '100%', offset: 0.5, easing: 'ease-in' },
			{ transform: 'translateY(50%)', opacity: '0%' },
		]
	}

	onMount(() => {
		socket.onOverlayMessageRecieved = function(message: OverlayMessage) {
			overlayText = message.str;
			overlayFgStyle = message.fillStyle;
			overlay.animate(animations[message.animation],
				{ duration: message.duration * 1000 });
		}

		canvas.width = canvas.clientWidth;
		canvas.height = canvas.clientHeight;

		let resetButton: {rect: Rectangle, fillProgress: number, touchStartTime: DOMHighResTimeStamp | null};
		let playingField: PlayingField;

		{
			let preferredResetBtnHeight = calculatePreferredResetBtnHeight(canvas);
			let actualBlockSize = canvas.width/scene.level.width;
			let levelHeight = Math.floor((canvas.height - preferredResetBtnHeight) / actualBlockSize);

			playingField = new PlayingField(scene.level, levelHeight, {x: 0, y: 3});

			resetButton = {
				rect: new Rectangle(0, levelHeight * actualBlockSize, canvas.width, canvas.height),
				fillProgress: 0,
				touchStartTime: null
			};
		}

		let previousFillCount = 0;
		let alreadyAnnouncedDone = false;

		let previousTouchPosition: {x: number, y: number} = null;
		let isTouchDown = false;

		canvas.ontouchstart = (e: TouchEvent)=>{
			e.preventDefault();
			let touchPosition = {x: e.touches[0].clientX, y: e.touches[0].clientY};
			isTouchDown = true;
			if (resetButton.rect.contains(touchPosition))
				resetButton.touchStartTime = Date.now();
			
			//socket.sendAnnounceDone();
			previousTouchPosition = touchPosition;
		};

		canvas.ontouchmove = (e: TouchEvent)=>{
			e.preventDefault();
			let touchPosition = {x: e.touches[0].clientX, y: e.touches[0].clientY};

			let deltaX = touchPosition.x-previousTouchPosition.x;
			let deltaY = touchPosition.y-previousTouchPosition.y;

			if ((deltaX * deltaX + deltaY * deltaY)) {
				if (Math.abs(deltaX) > Math.abs(deltaY))
					playingField.setPlayerSpeed(Math.sign(deltaX) * 60, 0.0);
				else
					playingField.setPlayerSpeed(0.0, Math.sign(deltaY) * 60);
			}

			previousTouchPosition = touchPosition;

			if (!resetButton.rect.contains(touchPosition))
				resetButton.touchStartTime = null;
		};

		canvas.ontouchend = (e: TouchEvent)=>{
			isTouchDown = false;
			resetButton.touchStartTime = null;
		};

		const ctx: CanvasRenderingContext2D = canvas.getContext('2d');
		let frame: number;

        let startTime: number;
        let previousTime: number;

		function loop(time: DOMHighResTimeStamp) {
			frame = requestAnimationFrame(loop);
			time /= 1000.0;

			if (startTime == undefined)
                startTime = time;

            if (previousTime == undefined)
                previousTime = time;

            let deltaTime = time - previousTime;

            previousTime = time;

            if (deltaTime == 0)
                deltaTime = 1.0 / 60.0;

			let fps = 1.0/deltaTime;


			ctx.clearRect(0, 0, canvas.width, canvas.height);

			let scaling = getLevelSizeFactor();
			function rectLTRB(l: number, t: number, r: number, b: number, path: Path2D=null) {
				l = Math.round(l * scaling);
				t = Math.round(t * scaling);
				r = Math.round(r * scaling);
				b = Math.round(b * scaling);

				if (path!=null)
					path.rect(l, t, r-l, b-t);
				else
					ctx.fillRect(l, t, r-l, b-t);
			}
			function rect(x: number, y: number, w: number, h: number, path: Path2D=null) {
				rectLTRB(x, y, x+w, y+h, path);
			}
			function ellipseLTRB(l: number, t: number, r: number, b: number, path: Path2D=null) {
				l = Math.round(l * scaling);
				t = Math.round(t * scaling);
				r = Math.round(r * scaling);
				b = Math.round(b * scaling);
				ctx.beginPath();
				ctx.ellipse((l+r)/2, (t+b)/2, (r-l)/2, (b-t)/2, 0, 0, Math.PI * 2);
				ctx.closePath();
				ctx.fill();
			}
			function ellipse(x: number, y: number, w: number, h: number, path: Path2D=null) {
				ellipseLTRB(x, y, x+w, y+h);
			}

			//#region Level
			playingField.update(deltaTime);

			if(!alreadyAnnouncedDone && playingField.isDone()) {
				socket.sendAnnounceDone();
				alreadyAnnouncedDone = true;
			}

			let blocksLighter = new Path2D();
			let blocksDarker = new Path2D();
			let colorBlocks = new Path2D();
			let voidMask = new Path2D();

			let fillCount = 0;
			for (let x = 0; x < playingField.getWidth(); x++) {
				for (let y = 0; y < playingField.getHeight(); y++) {
					switch (playingField.getBlockAt(x, y)) {
						case BlockTypes.Empty:
							rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, voidMask);
							break;
						case BlockTypes.Solid:
							if (x % 2 == y % 2)
								rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, blocksLighter);
							else
								rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, blocksDarker);
							break;
						case BlockTypes.Filled:

							ctx.fillStyle = "#f55";
							rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, colorBlocks);
							fillCount++;
							break;
						default:
							break;
					}
				}
			}

			if (previousFillCount!=fillCount) {
				socket.sendAnnounceProgress(scene.level);
				previousFillCount = fillCount;
			}

			let hue = (scene.level.id-1)*30;
			let glowStrength = 0.5+Math.sin(time)*0.5;
			let brightness = scene.level.brightness;

			const steps = 10;

			ctx.lineJoin = "round";
			ctx.strokeStyle = `hsl(${hue}, 100%, 70%, ${100 / steps * glowStrength}%)`;

			for (let i = 1; i <= steps; i++) {
				let t=i/steps;

				let inv_f = Math.sqrt(1/t);

				ctx.lineWidth = t*16;
				ctx.stroke(colorBlocks);
			}

			ctx.fillStyle = "#000";
			ctx.fill(voidMask);

			ctx.fillStyle = `hsl(${hue}, 100%, 70%)`;
			ctx.fill(colorBlocks);

			ctx.fillStyle = `hsl(0, 0%, 30%, ${Math.round(100*brightness)}%)`;
			ctx.fill(blocksDarker);
			ctx.fillStyle = `hsl(0, 0%, 50%, ${Math.round(100*brightness)}%)`;
			ctx.fill(blocksLighter);

			let playerPosition = playingField.getPlayerPosition();
			ctx.fillStyle = ctx.strokeStyle = `hsl(${hue}, 100%, 30%)`;
			ellipse(playerPosition.x * BLOCK_SIZE,
				playerPosition.y * BLOCK_SIZE,
				BLOCK_SIZE, BLOCK_SIZE);
			//#endregion
			
			//#region Level Title
			{
				let t = 0;
				let b = scaling * BLOCK_SIZE * 3;
				let fontSize = Math.round((b-t)*0.9);
				ctx.font = `${fontSize}px Arial-Rounded Bold`;
				ctx.textAlign = "center";
				ctx.textBaseline = "middle";
				ctx.fillStyle = "#0008";
				rectLTRB(0, 0, playingField.getWidth()*BLOCK_SIZE, 3*BLOCK_SIZE);
				ctx.fillStyle = ctx.strokeStyle = `hsl(${hue}, 100%, 70%)`;
				ctx.fillText(scene.level.name, canvas.width/2, (t+b)/2 + fontSize*0.1);
			}
			//#endregion

			//#region Reset Button
			
			if(resetButton.touchStartTime!=null) {
				let heldTimeSeconds = (Date.now()-resetButton.touchStartTime) / 1000.0;
				resetButton.fillProgress = Math.min(heldTimeSeconds/2.0, 1.0);
			}
			else{
				resetButton.fillProgress = 0.0;
			}

			let r = {...resetButton.rect};
			ctx.fillStyle = "#900";
			ctx.fillRect(r.left, r.top, 
					r.right - r.left,
					r.bottom - r.top);

			let fontSize = Math.round(resetButton.rect.getHeight()*0.4);
			ctx.font = `${fontSize}px Arial-Rounded Bold`;
			ctx.scale(0.9, 1.0);
			ctx.translate(canvas.width/2*(1/0.9-1), 0);
			ctx.fillStyle = "#f00";
			ctx.textAlign = "center";
			ctx.textBaseline = "middle";
			ctx.fillText("RESET POSITION", canvas.width/2, (resetButton.rect.top + resetButton.rect.bottom)/2);
			ctx.resetTransform();

			let t = Math.pow(resetButton.fillProgress, 0.2);
			r.bottom = (1-t) * r.bottom + t * r.top;
			ctx.fillStyle = "#0005";
			ctx.fillRect(r.left, r.top, 
					r.right - r.left,
					r.bottom - r.top);

			if (resetButton.fillProgress==1.0) {
				resetButton.fillProgress = 0.0;
				resetButton.touchStartTime = null;
				playingField.resetPlayerPosition();
			}
			//#endregion

			ctx.font = `14px Consolas`;
			ctx.textAlign = "left";
			ctx.textBaseline = "top";
			ctx.fillStyle = "#fff9";
			ctx.fillText(`fps: ${fps.toFixed(0)}`, 10, 10);
		};

		frame = requestAnimationFrame(loop);

		return () => {
			cancelAnimationFrame(frame);
		};
	});
</script>

<div class="center-content" style="grid-template-rows: 1fr;">
    <canvas bind:this={canvas} width={32} height={32} style="width: 100%; height: 100%">
		Your Browser doesn't support Canvas
	</canvas>
</div>
<div bind:this={overlay} class="overlay" style="transform:translateY(-100%)">
	<div>
		<p style="color: {overlayFgStyle}">
			{overlayText}
		</p>
	</div>
</div>


<style>
	.overlay {
		pointer-events: none;
		position: absolute;
		inset: 0;

		display: grid;
		align-content: center;
    	align-items: center;
		font-size: 2em;
	}

	.overlay > div {
		background: rgba(0, 0, 0, 50%);
		border: solid 0.5em transparent;
	}

	.overlay > div > p {
		margin: 0;
	}

	.center-content {
		display: grid;
		width: 100%;
		height: 100%;
		align-content: center;
		justify-items: stretch;
    	align-items: stretch;
	}

	canvas {
		-webkit-touch-callout: none;
		-webkit-user-select: none;
		-khtml-user-select: none;
		-moz-user-select: none;
		-ms-user-select: none;
		user-select: none;
		outline: none;
		-webkit-tap-highlight-color: rgba(255, 255, 255, 0); /* mobile webkit */
	}
</style>