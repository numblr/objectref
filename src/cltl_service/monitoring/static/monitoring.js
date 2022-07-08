$(document).ready(function () {
    let load_data = function () {
        $("#error_message").empty();

        $.get("../text", function (msg, status) {
            if (status !== 200 && status !== "success") {
                console.log("Failed to load utterance", status);
                $("#error_message").append("Failed (" + status + ")to load text: " + msg);

                return;
            }

            console.debug("Received text", msg);

            $("#utterance").html(msg['speaker'] + "> " + msg['utterance']);
        });

        $("#camera_view").onload = function () {
            console.debug("Reloaded image");
        };
        $("#camera_view").attr("src", "../image#" + new Date().getTime());
    };

    setInterval(load_data, 2500);
});