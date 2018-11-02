const express = require("express");
const child_process = require("child_process");

const app = express();
var stream1Proc = null;
var Buffer = "";
function stream1(req, res){
    try{
        //res.header("Content-Type", "application/octet-stream");
        var total = 0;
        res.writeHead(206, {
            "Content-Type": "application/octet-stream",
            
        });
        if(stream1Proc == null){
            stream1Proc = child_process.spawn("ffmpeg", "-f v4l2 -framerate 10 -video_size 640x480 -i /dev/video2 -c:v libx264 -b:v 256k -f h264 -".split(" "));
            stream1Proc.stdout.setEncoding("hex");
            stream1Proc.stdout.on("readable", () => {
                var data =  stream1Proc.stdout.read();
                Buffer += data;
                if(Buffer.indexOf("00000001", 8) > -1){
                    data = Buffer.substr(0, Buffer.indexOf("00000001", 8));
                    Buffer = Buffer.substr(Buffer.indexOf("00000001", 8));
                    res.write(data);
                }
                
                
            });
        }
    }
    catch(e){

    }
}


app.use("/", express.static(__dirname));

app.get("/streams/stream1.raw", stream1);

app.listen(8090);