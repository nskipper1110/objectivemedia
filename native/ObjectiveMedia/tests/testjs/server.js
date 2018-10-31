const express = require("express");
const child_process = require("child_process");

const app = express();
var stream1Proc = null;
var stream1Buf = [];
function stream1(req, res){
    try{
        //res.header("Content-Type", "application/octet-stream");
        var total = 0;
        res.writeHead(200, {
            "Content-Type": "application/octet-stream",
            
        });
        if(stream1Proc == null){
            stream1Proc = child_process.spawn("ffmpeg", "-f v4l2 -framerate 10 -video_size 640x480 -i /dev/video2 -c:v libx264 -b:v 256k -f h264 -".split(" "));
            stream1Proc.stdout.on("readable", () => {
                setImmediate(function(){
                    var data =  stream1Proc.stdout.read();
                    stream1Buf.push(data);
                });
                
            });
        }
        while(stream1Buf.length > 1){
            res.write(stream1Buf.shift());
        }
        if(stream1Buf.length > 0){
            res.end(stream1Buf.shift());
        }
        
        
    }
    catch(e){

    }
}


app.use("/", express.static(__dirname));

app.get("/streams/stream1.raw", stream1);

app.listen(8090);