// types: 'primary', 'info', 'success', 'warning', 'danger'
let tools = {
  showNotification: function (from, align, message, type) {
    $.notify({
      icon: "add_alert",
      message: message
    }, {
      type: type,
      timer: 3000,
      placement: {
        from: from,
        align: align
      }
    });
  },
  maskCard: function (e) {
    let n=e.textContent,l=n.replace(/\s+/g,"").replace(/[^0-9]/gi,"").match(/\d{4,16}/g),t=l&&l[0]||"",g=[];for(i=0,len=t.length;i<len;i+=4)g.push(t.substring(i,i+4));return g.length?g.join(" "):n;
  }
};