let ws;
let connected = false;
let latest_hum = 0.0;
let latest_temp = 0.0;
let counter = 0;
let interval_multi_reads = 0;
let ten_reads = new Array(10);
let alarm_temp = 60;
let alarm_hum = 25;
function open_websocket() {
  const status_msg = document.querySelector(".ws-status-text");
  const ws_btn = document.querySelector("#ws-connect-btn");

  if (!connected){
    ws = new WebSocket("ws://localhost:8888/ws/");
    status_msg.innerHTML = "Connecting...";
  } else {
    connected = false;
    ws.close();
    ws_btn.innerHTML = "Connect to Websocket";
    status_msg.innerHTML = "Websocket Closed";
    enable_sensor_ui(false);
  }

  ws.addEventListener("open", (event) => {
    console.log(event.data);
    ws.send("Hello Server!");
    status_msg.innerHTML = "Sucessfully Opened";
    connected = true;
    enable_sensor_ui(true);
    ws_btn.innerHTML = "Disconnect Websocket";
    request_data();
  });

  ws.addEventListener("message", (event) => {
    console.log("Message from server ", event.data);
    const [msg_type, msg_val] = event.data.split(" ", 2);
    switch(msg_type) {
      case "data":
        [latest_hum, latest_temp, latest_dt] = parse_humtemp_data(msg_val);
      case "datam":
        [latest_hum, latest_temp, latest_dt] = parse_humtemp_data(msg_val);
        ten_reads[counter] = [latest_hum, latest_temp, latest_dt];
    }    
  });

  ws.addEventListener("error", (event) => {
    console.log("Error occurred ", event.data);
    if (!connected) {
      status_msg.innerHTML = "Error on connection.";
    }
    status_msg.innerHTML = "Error!";
  });
}

/**
* Sends a websocket data request to the server to receive
* humidity and temperature data
*/
function request_data(for_multiple){
  if(!for_multiple){
    ws.send("data req");
  } else {
    ws.send("datam req");   
  }
}

/**
* Parses the data values of a data message into the humidity and temperature
* values from the sensor
* 
* Returns a two-element array with humidity in the first index and temp in the
* second
* @param {string} data_value - humidity,temperature string value from ws
* @returns {Array} hum_temp - array with humidity and temperature as float
*/
function parse_humtemp_data(data_value){
  const values = data_value.split(",");
  hum = parseFloat(values[0]);
  temp = parseFloat(values[1]);
  dt = values[2];
  return [hum, temp, dt];  
}

/**
* Enables all the buttons that can request data. This needs to happen after
* the websocket connection is successfully opened. Otherwise a websocket error
* will occur when data requests are sent
* @param {boolean} enable - enable (true) or disable (false) the sensor UI
*/
function enable_sensor_ui(enable){
  const sensor_btns = document.querySelectorAll(".sensor-btn");

  for (const btn of sensor_btns) {
    btn.disabled = !enable;
  }
}

function get_single_read(){
  request_data(false);
  const hum_p = document.querySelector("#single-hum");
  const temp_p = document.querySelector("#single-temp");

  hum_p.innerHTML = latest_hum.toFixed(2);
  temp_p.innerHTML = latest_temp.toFixed(2);
}

function get_ten_reads(){
  request_data(true);
  // console.log("temp: ", latest_temp, " hum: ", latest_hum);
  update_table(counter);
  counter++;
  if(counter >= 10) {
    counter = 0;
    clearInterval(interval_multi_reads);
  }  
  console.log("counter:", counter);
}
function start_multi_read(){
  interval_multi_reads = setInterval(() =>  {get_ten_reads()}, 1000);
}

function update_table(row){
  const rows = document.querySelectorAll(".data-row");

  const td = rows[row].children;

  td[0].innerHTML=ten_reads[row][0].toFixed(2);
  td[1].innerHTML=ten_reads[row][1].toFixed(2);
  td[2].innerHTML=ten_reads[row][2];
  
}

alarm_form = document.getElementById("alarm-form");

alarm_form.addEventListener("submit", (event) => {
  event.preventDefault();
  if(!connected) {
    return;
  }
  alarm_temp_value = document.getElementById("temp-alarm").value;
  alarm_hum_value = document.getElementById("hum-alarm").value;
  msg = "alarm ".concat(alarm_temp_value,",",alarm_hum_value);
  ws.send(msg);
});
