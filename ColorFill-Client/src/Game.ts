import type { Level } from "./App";

export function calculatePreferredResetBtnHeight(screenSize: {width: number, height: number}) {
    return screenSize.width/4.0;
}

export function calculateLevelSizeRatio(screenSize: {width: number, height: number}) {
    return (screenSize.height-calculatePreferredResetBtnHeight(screenSize)) / screenSize.width;
}

export const BlockTypes = {
    Empty: 0,
    Solid: 1,
    Filled: 2
};

export class Rectangle {
    constructor(public left: number, public top: number, 
                public right: number, public bottom: number) {

    }

    public contains(point: {x: number, y: number}) {
        return this.left <=point.x && point.x <=this.right &&
               this.top <=point.y && point.y <=this.bottom;
    }

    public getWidth() {
        return this.right-this.left;
    }

    public getHeight() {
        return this.bottom-this.top;
    }
}

export class PlayingField {
    player: {x: number, y: number, speedX: number, speedY: number};

    constructor(private level: Level, private height: number, private playerStartPosition: {x: number, y: number}) {
        this.player = 
        {
            x: playerStartPosition.x,
            y: playerStartPosition.y,
            speedX: 0, speedY: 0
        };

        if (level.width*height > level.blocks.length) {
            level.blocks = level.blocks.concat(
                Array(level.width*height - level.blocks.length).fill(1));
        }

        this.setBlockAt(this.player.x, this.player.y, BlockTypes.Filled);
    }

    public getWidth() {
        return this.level.width;
    }

    public getHeight() {
        return this.height;
    }

    public resetPlayerPosition() {
        this.player.x = this.playerStartPosition.x;
        this.player.y = this.playerStartPosition.y;
        this.player.speedX = 0.0;
        this.player.speedY = 0.0;
    }

    public setPlayerSpeed(x: number, y: number) {
        if(this.player.speedX!=0.0 || this.player.speedY!=0.0)
            return;

        this.player.speedX = x;
        this.player.speedY = y;
    }

    public getPlayerPosition() {
        return {
            x: this.player.x, 
            y: this.player.y
        }
    }

    public isDone(): boolean {
        for (let block of this.level.blocks) {
            if (block == BlockTypes.Empty)
                return false;
        }

        return true;
    }
    
    public update(deltaTime: number) {
        let deltaX = this.player.speedX * deltaTime;
        let deltaY = this.player.speedY * deltaTime;
        let steps = Math.ceil(Math.max(Math.abs(deltaX), Math.abs(deltaY))/0.49);

        for (let i = 0; i < steps; i++) {
            this.player.x += deltaX / steps;
            this.player.y += deltaY / steps;

            let checkDirX = Math.sign(deltaX);
            let checkDirY = Math.sign(deltaY);

            let fieldX = Math.round(this.player.x) + checkDirX;
            let fieldY = Math.round(this.player.y) + checkDirY;

            if (this.isSolid(fieldX, fieldY)) {
                // resolve collision
                this.player.x = fieldX - checkDirX;
                this.player.y = fieldY - checkDirY;

                if (this.getBlockAt(this.player.x, this.player.y) == BlockTypes.Empty)
                    this.setBlockAt(this.player.x, this.player.y, BlockTypes.Filled);

                this.player.speedX = 0.0;
                this.player.speedY = 0.0;
                console.log("Stop");
                break;
            }

            this.setBlockAt(Math.round(this.player.x), Math.round(this.player.y), BlockTypes.Filled);
        }
    }

    public getBlockAt(x: number, y: number) {
		return this.level.blocks[x+y*this.level.width];
	}

	private setBlockAt(x: number, y: number, block: number) {
		this.level.blocks[x+y*this.level.width] = block;
	}

    private isSolid(x, y) {
        return x < 0 || x >= this.getWidth() || y < 0 || y >= this.getHeight() || 
        this.getBlockAt(x, y) == BlockTypes.Solid;
    }
}