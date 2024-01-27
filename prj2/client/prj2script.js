let ws;
let connected = false;
let latest_hum = 0.0;
let latest_temp = 0.0;
let counter = 0;
let interval_multi_reads = 0;
let ten_reads = new Array(10);
let alarm_temp = 60;
let alarm_hum = 25;
let alarm_temp_crossed = false;
let alarm_hum_crossed = false;
let temp_stats = new Array(3);
let hum_stats = new Array(3);
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
  });

  ws.addEventListener("message", (event) => {
    console.log("Message from server ", event.data);
    const [msg_type, msg_val] = event.data.split(" ", 2);
    switch(msg_type) {
      case "data":
        [latest_hum, latest_temp, latest_dt] = parse_humtemp_data(msg_val);
        update_single_read_ui();
        update_alarms();
        break;
      case "datam":
        [latest_hum, latest_temp, latest_dt] = parse_humtemp_data(msg_val);
        ten_reads[counter] = [latest_hum, latest_temp, latest_dt];
        update_table_ui(counter);
        update_counter();
        update_alarms();
        break;
      case "datacalc":
        let res = parse_calc_data(msg_val);
        temp_stats[0] = res[0][0];       
        temp_stats[1] = res[0][1];       
        temp_stats[2] = res[0][2];       
        hum_stats[0] = res[1][0];       
        hum_stats[1] = res[1][1];       
        hum_stats[2] = res[1][2];       
        update_stats_table();
        break;
    }    
  });

  ws.addEventListener("error", (event) => {
    console.log("Error occurred ", event.data);
    if (!connected) {
      status_msg.innerHTML = "Error on connection.";
    }
    status_msg.innerHTML = "Error!";
    enable_sensor_ui(false);
  });

  ws.addEventListener("close", (event) => {
    console.log("Closing ", event.data);
    connected = false;
    status_msg.innerHTML = "Disconnected/Closed";
    enable_sensor_ui(false);
  });
}

/**
* Simple check to make sure we cannot send messages is the 
* socket is not ready to send
*/
function is_ws_open(ws) {
  return ws.readyState === ws.OPEN;
}

/**
* Sends a websocket data request to the server to receive
* humidity and temperature data
* @param {boolean} for_multiple - determines if the data sent is meant for the
* single read or multi-read ui elements
*/
function request_data(for_multiple){
  if(!is_ws_open(ws)) return;
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
* Parses the data values of a data message into the humidity and temperature
* values from the sensor
* 
* Returns a two-element array of arrays, first index for the temperature values
* and the second for the humidity values 
* @param {string} data_value - humidity,temperature string value from ws
* @returns {Array} temp_hum - [[min,max,avg],[min,max,avg]]
*/
function parse_calc_data(data_value){
  let results = new Array(2);
  let values = data_value.split(",").map((el) => parseFloat(el));
  results[0] = values.slice(0,3);
  results[1] = values.slice(3);
  return results;
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
}

function update_single_read_ui(){
  const hum_p = document.querySelector("#single-hum");
  const temp_p = document.querySelector("#single-temp");

  hum_p.innerHTML = latest_hum.toFixed(2);
  temp_p.innerHTML = latest_temp.toFixed(2);
}

function get_ten_reads(){
  request_data(true);
  console.log(ten_reads);
}
function start_multi_read(){
  interval_multi_reads = setInterval(() =>  {get_ten_reads()}, 1000);
}

function update_table_ui(row){
  const rows = document.querySelectorAll(".data-row");

  const td = rows[row].children;

  td[0].innerHTML=ten_reads[row][0].toFixed(2);
  td[1].innerHTML=ten_reads[row][1].toFixed(2);
  td[2].innerHTML=ten_reads[row][2];
}

function update_counter(){
  counter++;
  if(counter == 10) {
    counter = 0;
    clearInterval(interval_multi_reads);
  }  
}

alarm_form = document.getElementById("alarm-form");

alarm_form.addEventListener("submit", (event) => {
  event.preventDefault();
  alarm_temp = document.getElementById("temp-alarm").value;
  alarm_hum = document.getElementById("hum-alarm").value;
});

function check_temp_alarm(){
  return latest_temp > alarm_temp;
}

function check_hum_alarm(){
  return latest_hum > alarm_hum;
}

/**
* Updates the alarm UI elements when an sensor data has crossed the 
* threshold
*/
function update_alarms(){
  const alarm_temp_notif = document.querySelector("#temp-notif");
  const alarm_hum_notif = document.querySelector("#hum-notif")

  if(check_temp_alarm() && !alarm_temp_crossed){
    alarm_temp_crossed = true;
    alarm_temp_notif.innerHTML="ALARM AT ".concat(latest_temp.toFixed(2),"degC");
  }
  if(check_hum_alarm() && !alarm_hum_crossed){
    alarm_hum_crossed = true;
    alarm_hum_notif.innerHTML="ALARM AT ".concat(latest_hum.toFixed(2),"%");
  }
}

function get_stats(){
  if(!connected || !is_ws_open(ws)){
    return;
  }
  ws.send("calcstats");
}

/**
* Updates the stats table UI when the calc stats button is pressed
*/
function update_stats_table(){
  const rows = document.querySelectorAll(".calc-row");

  let temp_row = rows[0].children;
  let hum_row = rows[1].children;

  temp_row[1].innerHTML = temp_stats[0].toFixed(2);
  temp_row[2].innerHTML = temp_stats[1].toFixed(2);
  temp_row[3].innerHTML = temp_stats[2].toFixed(2);
  hum_row[1].innerHTML  = hum_stats[0].toFixed(2);
  hum_row[2].innerHTML  = hum_stats[1].toFixed(2);
  hum_row[3].innerHTML  = hum_stats[2].toFixed(2);
}

function close_app(){
  if(connected && is_ws_open(ws)){
    ws.send("shutdown");
  }

  close();
}
