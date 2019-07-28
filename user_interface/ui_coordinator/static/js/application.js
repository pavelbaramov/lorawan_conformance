$(document).ready(function () {
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var display_msg_received = [];

    //receive details from server
    socket.on('display_gui', function (msg) {
        console.log("Display message on gui " + msg);
        display_msg_received.push(msg);
        show_str = "";
        for (var i = 0; i < display_msg_received.length; i++) {
            show_str = show_str + display_msg_received[display_msg_received.length - 1 - i];
        }
        $('#test_details').html(show_str);
    });

    socket.on('user_alerts', function (msg) {
        console.log("Show user alert: " + msg);
        $('#user_alerts').html(msg);
    });

    socket.on('enable_dut_button', function (msg) {
        console.log("Enable DUT ABP config form.");
        $('#test_control').show();

        $('#device_config').show();
    });

    $('#device_config_form').submit(function (event) {
        console.log("clicked device submit");

        event.preventDefault();
        let dev_addr_in = $('#dev_addr').val();
        let dev_eui_in = $('#dev_eui').val();
        let app_key_in = $('#app_key').val()
        socket.emit('get_device_from_gui', {
            dev_addr: dev_addr_in,
            dev_eui: dev_eui_in,
            app_key: app_key_in
        });
        $('#device_config').hide();
        $('#device_show').show();
        $('#show_dev_eui').append(dev_eui_in);
        $('#show_dev_addr').append(dev_addr_in);
        $('#show_app_key').append(app_key_in);
        return false;
    });

    socket.on('enable_start_button', function (msg) {
        console.log("Enable START button form.");
        $('#start_testing').show();
    });

    $('#start_testing_form').submit(function (event) {
        console.log("clicked START button");

        event.preventDefault();

        socket.emit('start_button_pressed', "");
        $('#start_testing').hide();
        return false;
    });

});
