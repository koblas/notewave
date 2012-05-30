var transmission_errors = 0;
var first_poll = true;

//process updates if we have any, request updates from the server,
// and call again with response. the last part is like recursion except the call
// is being made from the response handler, and not at some point during the
// function's execution.
function longPoll() {
  if (transmission_errors > 2) {
    return;
  }

  //make another request
  $.ajax({ cache: false
         , type: "GET"
         , url: "/waiter"
         , dataType: "json"
         // , data: { since: CONFIG.last_message_time, id: CONFIG.id }
         , error: function () {
             console.log("", "long poll error. trying again...", new Date(), "error");
             transmission_errors += 1;
             //don't flood the servers on error, wait 10 seconds before retrying
             setTimeout(longPoll, 10*1000);
           }
         , success: function (data) {
             transmission_errors = 0;
             //if everything went well, begin another request immediately
             //the server will take a long time to respond
             //how long? well, it will wait until there is another message
             //and then it will return it to us and close the connection.
             //since the connection is closed when we get data, we longPoll again
             if (data) 
                 _do_update(data.actions, null);
             longPoll();
           }
     });
}
