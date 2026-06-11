(function() {
  var socket = io({ transports: ['websocket', 'polling'] });

  socket.on('nouvelle_notification', function(data) {
    var dots = document.querySelectorAll('.bell-dot');
    dots.forEach(function(d) { d.style.display = data.nb_non_lues > 0 ? '' : 'none'; });
  });

  socket.on('new_message', function(data) {
    var chat = document.getElementById('chatMessages');
    if (!chat) return;
    var userId = document.getElementById('userId');
    var myId = userId ? parseInt(userId.value, 10) : 0;
    var isMe = data.expediteur_id === myId;
    var div = document.createElement('div');
    div.className = isMe ? 'msg-sent' : 'msg-received';
    var h = '';
    if (!isMe)
      h += '<div class="msg-avatar" style="background:var(--blue-100);color:var(--blue-600);overflow:hidden">' + (data.avatar_url ? '<img src="' + data.avatar_url + '" alt="" style="width:100%;height:100%;border-radius:50%;object-fit:cover" />' : data.prenom.charAt(0) + data.nom.charAt(0)) + '</div>';
    h += '<div>';
    if (!isMe)
      h += '<div style="font-size:.75rem;color:var(--slate-500);margin-left:4px;margin-bottom:2px">' + data.prenom + ' ' + data.nom + '</div>';
    h += '<div class="msg-bubble" style="padding:12px 16px;max-width:100%;' + (isMe ? 'background:var(--blue-600);color:white;border-radius:16px 16px 4px 16px' : 'background:white;border:1px solid var(--slate-200);border-radius:16px 16px 16px 4px') + '">' + data.contenu + '</div>';
    h += '<div style="font-size:.7rem;color:var(--slate-400);margin-top:4px;' + (isMe ? 'text-align:right' : 'margin-left:4px') + '">' + data.heure + '</div></div>';
    div.innerHTML = h;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  });

  var convId = document.getElementById('convId');
  if (convId) socket.emit('join_conversation', parseInt(convId.value, 10));

  var msgForm = document.getElementById('msgForm');
  if (msgForm) {
    msgForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var input = msgForm.querySelector('input[name="contenu"]');
      var btn = msgForm.querySelector('button[type="submit"]');
      var contenu = input.value.trim();
      if (!contenu) return;
      input.disabled = true; btn.disabled = true;
      socket.emit('send_message', { conv_id: parseInt(convId.value, 10), contenu: contenu }, function() {
        input.value = '';
        input.disabled = false; btn.disabled = false;
        input.focus();
      });
    });
  }
})();
