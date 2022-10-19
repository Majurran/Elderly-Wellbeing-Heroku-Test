// The four files chat.html, chat_style.css,chat_page.js and socketio.js come from Sandeep Sudhakaran at https://github.com/sandeepsudhakaran/rchat-app on the 12th of May 2019.
// The files are then modified to incorporate the elderly activities options and to be fit into the rest of the website.
// socketio.js and chat_style.css are standard file for running and designing chat rooms. 
document.addEventListener('DOMContentLoaded', () => {

    // Make 'enter' key submit message
    let msg = document.getElementById("user_message");
    msg.addEventListener("keyup", function(event) {
        event.preventDefault();
        if (event.keyCode === 13) {
            document.getElementById("send_message").click();
        }
    });
});
