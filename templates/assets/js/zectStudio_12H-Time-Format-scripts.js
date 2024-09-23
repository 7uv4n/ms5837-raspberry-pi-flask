var timePicker = document.getElementById('myTime');
function onTimeChange() {
  var timeSplit = timePicker.value.split(':'),
    hours,
    minutes,
    meridian;
  hours = timeSplit[0];
  minutes = timeSplit[1];
  if (hours > 12) {
    meridian = 'PM';
    hours -= 12;
  } else if (hours < 12) {
    meridian = 'AM';
    if (hours == 0) {
      hours = 12;
    }
  } else {
    meridian = 'PM';
  }
  document.getElementById('displayTime').innerHTML = (hours + ':' + minutes + ' ' + meridian);
}