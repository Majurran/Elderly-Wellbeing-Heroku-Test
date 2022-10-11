$(function () {
  $('#myCarousel').carousel({
      interval:12000,
      pause: "false"
  });
  
  $('#playButton').click(function () {
      $('#myCarousel').carousel('cycle');
  });
  $('#pauseButton').click(function () {
      $('#myCarousel').carousel('pause');
  });
});

// function produce_messages() {

//     var element = document.createElement("div");
//     element.appendChild(document.createTextNode('The man who mistook his wife for a hat'));
//     document.getElementById('lc').appendChild(element);

// }



$(document).ready(function() {
    setInterval(function () {

        start();
   }, 3000); 
});

function animateContent(direction) {  
    /* need to count for extra margin and stuff */
    var animationOffset = $('.project-container').height() - $('.content').height()-10;  /* padding */
    if (direction == 'up') {
        animationOffset = 10;
    }

    console.log("animationOffset:"+animationOffset);
    $('.content').animate({ "marginTop": (animationOffset)+ "px" }, 5000);
}

function up(){
    animateContent("up")
}
function down(){
    animateContent("down")
}

function start(){
 setTimeout(function () {
    down();
}, 2000);
 setTimeout(function () {
    up();
}, 2000);
   setTimeout(function () {
    console.log("wait...");
}, 5000);
}  
