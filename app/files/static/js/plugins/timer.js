let timer = {
  init: function (element_id, expired_at, redirect_url) {
    function seconds_to_timer(sec) {
      let sec_num = parseInt(sec);
      let hours   = Math.floor(sec_num / 3600);
      let minutes = Math.floor((sec_num - (hours * 3600)) / 60);
      let seconds = sec_num - (hours * 3600) - (minutes * 60);
      if (hours   < 10) {hours   = "0"+hours;}
      if (minutes < 10) {minutes = "0"+minutes;}
      if (seconds < 10) {seconds = "0"+seconds;}
      return hours+':'+minutes+':'+seconds;
    }
    let timer_container = document.getElementById(element_id);
    let now = Math.ceil(Date.now() / 1000);
    let expired_delta = expired_at - now;
    let timer = setInterval(function () {
      if (expired_delta <= 0) {
        clearInterval(timer);
        window.location.href = redirect_url;
      } else {
        timer_container.innerHTML = seconds_to_timer(expired_delta);
      }
      --expired_delta;
    }, 1000)
  }
}