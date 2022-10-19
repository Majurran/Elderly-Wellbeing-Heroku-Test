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
    document.getElementById("messages").animate([
        // keyframes
        { transform: 'translateY(0px)' },
        { transform: 'translateY(-50000px)' }
      ], {
        // timing options
        duration: 500000,
        iterations: 1
      });
});
