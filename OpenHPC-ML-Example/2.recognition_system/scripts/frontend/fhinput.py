import sys

def fhinput():
    return """
<canvas id="canvas" height="280px" width="280px" style="border: 1px solid black;"></canvas>
<p>
    <button id="clear">Clear</button>
    <button id="save">Save</button>
</p>
<p id="mesg"></p>

<script type="text/javascript">
    // ====== variables ====== //
    var kernel = IPython.notebook.kernel;
    var btn_clear = document.getElementById("clear");
    var btn_save = document.getElementById("save");
    var canvas = document.getElementById("canvas");
    var context = canvas.getContext("2d");

    var isDrawing = false;
    var x = 0;
    var y = 0;

    // ====== drawing ====== //
    // cf. https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event#examples
    canvas.addEventListener("mousedown", function(e){
        x = e.offsetX;
        y = e.offsetY;
        isDrawing = true;
    });
    
    canvas.addEventListener("mousemove", function(e){
        if (isDrawing === true) {
            drawLine(context, x, y, e.offsetX, e.offsetY);
            x = e.offsetX;
            y = e.offsetY;
        }
    });
    
    canvas.addEventListener("mouseup", function(e){
        if (isDrawing === true) {
            drawLine(context, x, y, e.offsetX, e.offsetY);
            x = 0;
            y = 0;
            isDrawing = false;
        }
    });
    
    canvas.addEventListener("mouseout", function(){
        x = 0;
        y = 0;
        isDrawing = false;
    });

    function drawLine(context, x1, y1, x2, y2) {
        context.beginPath();
        context.strokeStyle = 'black';
        context.lineWidth = 14;
        context.moveTo(x1, y1);
        context.lineTo(x2, y2);
        context.lineCap = "round";
        context.stroke();
    };

    // ====== button: clear ====== //
    btn_clear.addEventListener("click", function(){
        context.clearRect(0, 0, canvas.width, canvas.height);
        mesg.textContent = "";
    });
    
    // ====== button: save ====== //
    btn_save.addEventListener("click", function(){
        var img = 'base64_img';
        kernel.execute(img + " = '" + canvas.toDataURL() + "'");
        mesg.textContent = "image saved";
    });
      
</script>
"""



def fhinput2():
    return """
<canvas id="canvas2" height="280px" width="280px" style="border: 1px solid black;"></canvas>
<p>
    <button id="clear2">Clear</button>
    <button id="save2">Save</button>
    <button id="center2">Centralize & Save</button>
</p>
<p id="mesg2"></p>

<script type="text/javascript">
    // ====== variables ====== //
    var kernel = IPython.notebook.kernel;
    var btn_clear2 = document.getElementById("clear2");
    var btn_save2 = document.getElementById("save2");
    var btn_center2= document.getElementById("center2");
    var canvas2 = document.getElementById("canvas2");
    var context2 = canvas2.getContext("2d");

    var isDrawing = false;
    var x = 0;
    var y = 0;

    // ====== drawing ====== //
    // cf. https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event#examples
    canvas2.addEventListener("mousedown", function(e){
        x = e.offsetX;
        y = e.offsetY;
        isDrawing = true;
    });
    
    canvas2.addEventListener("mousemove", function(e){
        if (isDrawing === true) {
            drawLine(context2, x, y, e.offsetX, e.offsetY);
            x = e.offsetX;
            y = e.offsetY;
        }
    });
    
    canvas2.addEventListener("mouseup", function(e){
        if (isDrawing === true) {
            drawLine(context2, x, y, e.offsetX, e.offsetY);
            x = 0;
            y = 0;
            isDrawing = false;
        }
    });
    
    canvas2.addEventListener("mouseout", function(){
        x = 0;
        y = 0;
        isDrawing = false;
    });

    function drawLine(context2, x1, y1, x2, y2) {
        context2.beginPath();
        context2.strokeStyle = 'black';
        context2.lineWidth = 14;
        context2.moveTo(x1, y1);
        context2.lineTo(x2, y2);
        context2.lineCap = "round";
        context2.stroke();
    };

    // ====== button: clear ====== //
    btn_clear2.addEventListener("click", function(){
        context2.clearRect(0, 0, canvas2.width, canvas2.height);
        mesg2.textContent = "";
    });
    
    // ====== button: save ====== //
    btn_save2.addEventListener("click", function(){
        var img = 'base64_img';
        kernel.execute(img + " = '" + canvas2.toDataURL() + "'");
        mesg2.textContent = "image saved";
    });
   
    // ====== button: center ====== //
    btn_center2.addEventListener("click", function(){
        var t = canvas2.height;
        var l = canvas2.width;
        var r = b = 0;
        for(y=0; y<canvas2.height; y++){
            for(x=0; x<canvas2.width; x++){
                var pixel = context2.getImageData(x, y, 1, 1);
                var data = pixel.data;
                if(data[3]){
                    t = (y < t) ? y : t;
                    l = (x < l) ? x : l;
                    r = (r < x) ? x : r;
                    b = (b < y) ? y : b;
                }
            }
        }
        iw = r - l + 1;
        ih = b - t + 1;

        // meve drew image on center of draw area //
        var drawimg = context2.getImageData(l, t, iw, ih);
        context2.clearRect(0, 0, canvas2.width, canvas2.height);
        context2.putImageData(drawimg, canvas2.width/2 - iw/2, canvas2.height/2 - ih/2);
        
        // save image //
        var img = 'base64_img';
        kernel.execute(img + " = '" + canvas2.toDataURL() + "'");
        mesg2.textContent = "centralized and saved";
    });
   
</script>
"""

