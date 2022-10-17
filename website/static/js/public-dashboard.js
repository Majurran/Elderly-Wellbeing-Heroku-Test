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





$(document).ready(function() {
    setInterval(function () {
        console.log("Started")
        start();
   }, 500); 
});

function animateContent(direction) {  
    /* need to count for extra margin and stuff */
    var animationOffset = $('.project-container').height() - $('.content').height()-10;  /* padding */
    if (direction == 'up') {
        animationOffset = 10;
    }

    // console.log("animationOffset:"+animationOffset);
    $('.content').animate({ "marginTop": (animationOffset)+ "px" }, 5000 *75);
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
}, 500);
 setTimeout(function () {
    up();
}, 500);
   setTimeout(function () {
    console.log("wait...");
}, 5000);
}  
