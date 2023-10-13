export type Lobby = {players: {name: string, isReady: boolean}[]}
export type Level = {id: number, name: string, blocks: number[], width: number, brightness: number}
export type Message = {str: string, bgFillStyle: string, fgFillStyle: string}
export type OverlayMessage = {str: string, fillStyle: string, duration: number, animation: string}

export class ConnectingScene {}
export class LobbyScene {constructor(public lobby: Lobby) {}}
export class GameScene {constructor(public level: Level) {}}
export class MessageScene {constructor(public message: Message) {}}

export type Scene = ConnectingScene | LobbyScene | GameScene | MessageScene

export class SocketWrapper {
    onConnectionEstablished: () => void;
    onConnectionLost: () => void;
    onMessageRecieved: (message: Message) => void;
    onOverlayMessageRecieved: (message: OverlayMessage) => void;
    onLevelRecieved: (level: Level) => void;
    onLobbyRecieved: (lobby: Lobby) => void;

    constructor(private socket: WebSocket) {
        let self = this;
        socket.onopen = function() {
            console.log("WebSocket connection established.");

            self.onConnectionEstablished?.();
        };

        socket.onerror = function(ev: Event) {
            console.error("WebSocket error: " + ev);
        };

        socket.onclose = function(ev: CloseEvent) {
            console.log("WebSocket connection closed with code: " + ev.code);
            // setInterval(function () {location.reload()}, 1000);
            self.onConnectionLost?.();
        };

        socket.onmessage = function(ev: MessageEvent) {
            const message = ev.data as string;
            console.log("Received message: " + message);
            let match = message.match("^([a-zA-Z0-9_]*):([\\s\\S]*)$");
            
            if (match) {
                if(match[1] == "level") {
                    let parts = match[2].split(";");
                    let id = parseInt(parts[0]);
                    let name = parts[1];
                    let gridSizeX = parseInt(parts[2]);
                    let brightness = parseFloat(parts[3]);
                    let levelString = parts[4];

                    let blocks = levelString.split("").map(function(item) {
                        return parseInt(item, 10);
                    });

                    self.onLevelRecieved?.({id, name, blocks, width: gridSizeX, brightness});
                }
                else if (match[1] == "lobby") {
                    let players = [];
                    if (match[2].length > 0) {
                        for (const playerStr of match[2].split("\n")) {
                            let name = playerStr.substring(0, playerStr.length-1);
                            let isReady = playerStr[playerStr.length-1] == "+";
    
                            players.push({name, isReady})
                        }
                    }

                    self.onLobbyRecieved?.({players});
                }
                else if (match[1] == "message") {
                    let parts = match[2].split(";", 3);
                    let bgFillStyle = parts[0];
                    let fgFillStyle = parts[1];
                    let str = parts[2];

                    self.onMessageRecieved?.({str, fgFillStyle, bgFillStyle});
                }
                else if (match[1] == "overlay_message") {
                    let parts = match[2].split(";", 4);
                    let duration = parseFloat(parts[0]);
                    let animation = parts[1];
                    let fillStyle = parts[2];
                    let str = parts[3];

                    self.onOverlayMessageRecieved?.({str, fillStyle, duration, animation});
                }
            }
        }
    }

    public isOpen(): boolean {
        return this.socket.readyState == WebSocket.OPEN;
    }

    public sendRegisterPlayer(name: string, levelSizeRatio: number) {
        this.socket.send(`RegisterPlayer:${name}{levelSizeRatio=${levelSizeRatio}}`)
    }

    public sendRegisterPlayer_nameOnly(name: string) {
        this.socket.send(`RegisterPlayer:${name}`)
    }

    public sendAnnounceReady() {
        this.socket.send(`AnnounceReady:`)
    }

    public sendAnnounceDone() {
        this.socket.send(`AnnounceDone:`)
    }

    public sendAnnounceProgress(level: Level) {
        if (level!=null) {
            let levelBytes = new Uint8Array(Math.ceil(level.blocks.length / 4) * 4);
            levelBytes.set(level.blocks);
            let compressedLevelBytes = new Uint8Array(levelBytes.length/4);

            for(let i = 0; i<levelBytes.length; i+=4) {
                let byte = 0;
                byte |= levelBytes[i+0] << (2*0);
                byte |= levelBytes[i+1] << (2*1);
                byte |= levelBytes[i+2] << (2*2);
                byte |= levelBytes[i+3] << (2*3);
                compressedLevelBytes[i/4] = byte;
            }

            let levelHeight = level.blocks.length/level.width; 
            this.socket.send(`AnnounceProgress:${level.width};${levelHeight};${
                btoa(String.fromCharCode.apply(null, compressedLevelBytes))
            }`);
        }

    }

    public unsubscribeAll() {
        this.onConnectionEstablished = null;
        this.onMessageRecieved = null;
        this.onLevelRecieved = null;
        this.onLobbyRecieved = null;
    }
}