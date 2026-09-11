/* Чат-консультант BIM Pulse. Кнопка в углу, окно с историей, ответы от бэкенда /api/chat.

   Сессия — случайный токен в localStorage: история видна только в этом браузере,
   переживает перезагрузку и закрытие вкладки. Другие посетители её не увидят,
   сервер отдаёт историю только по токену. */

(function () {
  if (window.__bimChatLoaded) return;
  window.__bimChatLoaded = true;

  var API = '/api';
  var KEY = 'bimpulse_chat_session';
  var session = '';
  try { session = localStorage.getItem(KEY) || ''; } catch (e) { session = ''; }

  var root = document.createElement('div');
  root.className = 'bchat';
  root.innerHTML =
    '<button class="bchat-fab" type="button" aria-label="Открыть чат с консультантом">' +
      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-8 8H7l-4 3V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z"/></svg>' +
      '<span>Спросить</span>' +
    '</button>' +
    '<div class="bchat-win" hidden>' +
      '<div class="bchat-head">' +
        '<div><strong>Консультант BIM Pulse</strong><span>отвечает круглосуточно</span></div>' +
        '<button class="bchat-close" type="button" aria-label="Свернуть">×</button>' +
      '</div>' +
      '<div class="bchat-log" aria-live="polite"></div>' +
      '<form class="bchat-form">' +
        '<input type="text" name="_honey" class="bchat-honey" tabindex="-1" autocomplete="off" aria-hidden="true">' +
        '<textarea name="text" rows="1" maxlength="2000" placeholder="Опишите задачу…" required></textarea>' +
        '<button type="submit" aria-label="Отправить">' +
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/></svg>' +
        '</button>' +
      '</form>' +
      '<p class="bchat-note">Оставьте email или Telegram в сообщении — команда вернётся с разбором. Или сразу <a href="https://t.me/bim_pulse_ufa" target="_blank" rel="noopener">в Telegram</a>.</p>' +
    '</div>';
  document.body.appendChild(root);

  var fab = root.querySelector('.bchat-fab');
  var win = root.querySelector('.bchat-win');
  var log = root.querySelector('.bchat-log');
  var form = root.querySelector('.bchat-form');
  var input = form.querySelector('textarea');
  var loaded = false;

  function add(role, text) {
    var el = document.createElement('div');
    el.className = 'bchat-msg bchat-' + role;
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  function typing(on) {
    var t = log.querySelector('.bchat-typing');
    if (on && !t) {
      t = document.createElement('div');
      t.className = 'bchat-msg bchat-assistant bchat-typing';
      t.innerHTML = '<i></i><i></i><i></i>';
      log.appendChild(t);
      log.scrollTop = log.scrollHeight;
    } else if (!on && t) {
      t.remove();
    }
  }

  function loadHistory() {
    if (loaded) return;
    loaded = true;
    fetch(API + '/chat/history?session=' + encodeURIComponent(session), { credentials: 'omit' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.messages && d.messages.length) {
          d.messages.forEach(function (m) { add(m.role, m.content); });
        } else {
          add('assistant', d.welcome || 'Здравствуйте. Что у вас за задача?');
        }
      })
      .catch(function () {
        add('assistant', 'Здравствуйте. Опишите задачу — отвечу по существу.');
      });
  }

  function open() {
    win.hidden = false;
    fab.classList.add('is-open');
    loadHistory();
    setTimeout(function () { input.focus(); }, 50);
    try { window.ym && window.ym(111661242, 'reachGoal', 'chat_open'); } catch (e) {}
  }
  function close() {
    win.hidden = true;
    fab.classList.remove('is-open');
  }

  fab.addEventListener('click', function () { win.hidden ? open() : close(); });
  root.querySelector('.bchat-close').addEventListener('click', close);

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit', { cancelable: true }));
    }
  });
  input.addEventListener('input', function () {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  var busy = false;
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (busy) return;
    var text = input.value.trim();
    if (!text) return;
    add('user', text);
    input.value = '';
    input.style.height = 'auto';
    busy = true;
    typing(true);
    fetch(API + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'omit',
      body: JSON.stringify({ session: session, text: text, _honey: form.querySelector('.bchat-honey').value })
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        typing(false);
        if (d.session && d.session !== session) {
          session = d.session;
          try { localStorage.setItem(KEY, session); } catch (err) {}
        }
        add('assistant', d.reply || 'Не понял, переформулируйте, пожалуйста.');
        try { window.ym && window.ym(111661242, 'reachGoal', 'chat_message'); } catch (err) {}
      })
      .catch(function () {
        typing(false);
        add('assistant', 'Связь прервалась. Напишите нам в Telegram @bim_pulse_ufa — ответим руками.');
      })
      .finally(function () { busy = false; });
  });
})();
