/* Тест «Используете ли вы BIM на все 100%».
   Четыре вопроса, у каждого три уровня зрелости: 1 — модель живёт отдельно от процесса,
   2 — связь есть, но руками, 3 — данные ходят сами. Сумма 4–12 раскладывается на три
   вердикта, а в результат подставляются именно те направления, где человек ответил «1» —
   общий совет «внедряйте BIM» никому не нужен, нужен список своих дыр. */

(function () {
  const quiz = document.getElementById('quiz');
  if (!quiz) return;

  const YM_IDS = [109103460, 111661242];
  const goal = (name) => {
    YM_IDS.forEach((id) => {
      try { window.ym && window.ym(id, 'reachGoal', name); } catch (e) { /* блокировщик — не беда */ }
    });
  };

  const QUESTIONS = [
    {
      key: 'smeta',
      tag: 'Сметы и объёмы',
      title: 'Откуда берутся объёмы для сметы?',
      options: [
        {
          score: 1,
          title: 'Считаем по чертежам вручную',
          note: 'Сметчик меряет по планам, объёмы живут в своём файле.',
          feedback: 'Знакомо. Каждая правка планировки — это пересчёт с нуля, и расхождение со сметой находят уже на площадке.',
        },
        {
          score: 2,
          title: 'Выгружаем ведомости из модели',
          note: 'Спецификации в Excel, дальше сметчик переносит их в смету.',
          feedback: 'Уже быстрее, но Excel посередине — место, где теряется связь: модель поменялась, а выгрузка вчерашняя.',
        },
        {
          score: 3,
          title: 'Объёмы уходят в смету сами',
          note: 'Правка модели пересчитывает смету, расхождения видно сразу.',
          feedback: 'Это тот уровень, ради которого модель и строят. Дальше интереснее — насколько ей верят на стройке.',
        },
      ],
    },
    {
      key: 'ksg',
      tag: 'Календарный график',
      title: 'Как устроен КСГ — и знает ли о нём модель?',
      options: [
        {
          score: 1,
          title: 'График отдельно, модель отдельно',
          note: 'КСГ в Excel или MS Project, с моделью никак не связан.',
          feedback: 'Тогда график — это обещание, а не расчёт: сдвиг работ на объекте виден только на планёрке.',
        },
        {
          score: 2,
          title: 'Связываем руками по ключевым этапам',
          note: 'Разбиваем модель на захватки и подтягиваем сроки вручную.',
          feedback: 'Рабочий компромисс. Проблема в поддержке: пересобрать связи после изменений дороже, чем их сделать.',
        },
        {
          score: 3,
          title: '4D: график привязан к элементам',
          note: 'Видно, что построено к дате и где отставание.',
          feedback: 'Хорошо. Такой график можно показывать заказчику, не боясь вопроса «а откуда цифры?».',
        },
      ],
    },
    {
      key: 'kontrol',
      tag: 'Стройконтроль',
      title: 'Как фиксируете, что построено не по модели?',
      options: [
        {
          score: 1,
          title: 'Блокнот, телефон, чат',
          note: 'Замечания расходятся сообщениями, к модели не привязаны.',
          feedback: 'Замечание без привязки к элементу теряется первым. Через месяц никто не вспомнит, о какой оси шла речь.',
        },
        {
          score: 2,
          title: 'Замечания привязаны к элементам модели',
          note: 'Общая среда данных, у каждого дефекта — свой узел и статус.',
          feedback: 'Отличная база. Следующий шаг — сверять факт с моделью прямо на месте, а не по возвращении в офис.',
        },
        {
          score: 3,
          title: 'Сверяем через AR на площадке',
          note: 'Планшет накладывает модель на реальную конструкцию.',
          feedback: 'Немногие до этого дошли. Отклонение ловится в день работ, а не при приёмке.',
        },
      ],
    },
    {
      key: 'snab',
      tag: 'Снабжение',
      title: 'Как из модели рождается заявка на закуп?',
      options: [
        {
          score: 1,
          title: 'Заявку пишут текстом',
          note: 'Снабженец сам ищет позицию в номенклатуре и угадывает аналог.',
          feedback: 'Отсюда и пересорт: «труба стальная» в заявке и три разных позиции в счетах от поставщиков.',
        },
        {
          score: 2,
          title: 'Спецификация из модели → Excel → закуп',
          note: 'Перечень выгружаем, сопоставление с номенклатурой ручное.',
          feedback: 'Половина пути пройдена. Ручное сопоставление — то место, где объёмы ещё раз меняются по дороге.',
        },
        {
          score: 3,
          title: 'Элементы связаны с библиотекой номенклатуры',
          note: 'Заявка собирается по модели, позиции подставляются сами.',
          feedback: 'Тот случай, когда снабжение работает от модели, а не параллельно ей.',
        },
      ],
    },
  ];

  const LEVELS = [
    {
      max: 6,
      name: 'BIM как красивая картинка',
      lead: 'Модель есть, а решения принимаются мимо неё.',
      text: 'Скорее всего, вы уже платите за моделирование, но возвращаете вложенное только на визуализации и коллизиях. Всё, что дальше — объёмы, сроки, закуп — идёт по старым рельсам.',
    },
    {
      max: 9,
      name: 'BIM наполовину',
      lead: 'Данные из модели берут, но переносят руками.',
      text: 'Самый частый уровень. Модель уже кормит соседние процессы, но между ней и результатом стоит человек с Excel — и каждое изменение проекта стоит его рабочего дня.',
    },
    {
      max: 12,
      name: 'BIM работает на вас',
      lead: 'Модель — источник данных, а не приложение к проекту.',
      text: 'Вы в меньшинстве: у большинства до этого доходит один процесс из четырёх. Дальше растёт не охват, а точность — и то, насколько данным доверяют на площадке.',
    },
  ];

  const GAPS = {
    smeta: 'связать объёмы модели со сметой, чтобы правка планировки сразу меняла цифру',
    ksg: 'собрать 4D-график: работы привязаны к элементам, отставание видно на модели',
    kontrol: 'вывести стройконтроль на площадку — замечания на элементах, сверка через AR',
    snab: 'соединить модель с номенклатурой снабжения, чтобы заявка собиралась сама',
  };

  const stage = quiz.querySelector('[data-stage]');
  const bar = quiz.querySelector('[data-bar]');
  const counter = quiz.querySelector('[data-counter]');
  const startBtn = quiz.querySelector('[data-start]');
  const intro = quiz.querySelector('[data-intro]');

  const answers = [];
  let current = 0;
  let started = false;

  const iconFor = (qIndex, oIndex) =>
    document.getElementById(`icon-${QUESTIONS[qIndex].key}-${oIndex}`).innerHTML;

  /* Шапка липкая, поэтому scrollIntoView прячет верх карточки под неё —
     считаем позицию сами и оставляем запас. */
  function scrollToStage() {
    const y = stage.getBoundingClientRect().top + window.scrollY - 96;
    window.scrollTo({ top: Math.max(y, 0), behavior: 'smooth' });
  }

  function progress() {
    const done = answers.length;
    bar.style.width = `${(done / QUESTIONS.length) * 100}%`;
    counter.textContent = done < QUESTIONS.length
      ? `Вопрос ${current + 1} из ${QUESTIONS.length}`
      : 'Готово';
  }

  function renderQuestion() {
    const q = QUESTIONS[current];
    stage.innerHTML = `
      <div class="quiz-card" data-anim>
        <p class="quiz-tag">${q.tag}</p>
        <h2 class="quiz-question">${q.title}</h2>
        <div class="quiz-options">
          ${q.options.map((o, i) => `
            <button class="quiz-option" type="button" data-pick="${i}">
              <span class="quiz-option-art" aria-hidden="true">${iconFor(current, i)}</span>
              <span class="quiz-option-text">
                <strong>${o.title}</strong>
                <span>${o.note}</span>
              </span>
            </button>`).join('')}
        </div>
        <div class="quiz-feedback" data-feedback hidden></div>
      </div>`;
    progress();

    stage.querySelectorAll('[data-pick]').forEach((btn) => {
      btn.addEventListener('click', () => pick(Number(btn.dataset.pick), btn));
    });
  }

  function pick(index, btn) {
    if (btn.closest('.quiz-options').classList.contains('is-locked')) return;
    const q = QUESTIONS[current];
    const opt = q.options[index];
    answers[current] = { key: q.key, score: opt.score };

    const wrap = btn.closest('.quiz-options');
    wrap.classList.add('is-locked');
    wrap.querySelectorAll('.quiz-option').forEach((el) => el.classList.add('is-dim'));
    btn.classList.remove('is-dim');
    btn.classList.add('is-picked');

    const fb = stage.querySelector('[data-feedback]');
    const last = current === QUESTIONS.length - 1;
    fb.innerHTML = `
      <p>${opt.feedback}</p>
      <button class="btn" type="button" data-next>${last ? 'Показать результат' : 'Следующий вопрос'}</button>`;
    fb.hidden = false;
    fb.querySelector('[data-next]').addEventListener('click', () => {
      if (last) {
        renderResult();
      } else {
        current += 1;
        renderQuestion();
      }
      scrollToStage();
    });
    progress();
  }

  function renderResult() {
    const total = answers.reduce((sum, a) => sum + a.score, 0);
    const level = LEVELS.find((l) => total <= l.max);
    const gaps = answers.filter((a) => a.score < 3).map((a) => GAPS[a.key]);
    const percent = Math.round((total / (QUESTIONS.length * 3)) * 100);

    goal('quiz_finish');

    stage.innerHTML = `
      <div class="quiz-card quiz-result" data-anim>
        <p class="quiz-tag">Результат</p>
        <div class="quiz-score">
          <div class="quiz-score-num"><span data-count>0</span><i>%</i></div>
          <div class="quiz-score-text">
            <h2>${level.name}</h2>
            <p>${level.lead}</p>
          </div>
        </div>
        <div class="quiz-scale" aria-hidden="true"><span data-scale style="width:0%"></span></div>
        <p class="quiz-result-text">${level.text}</p>
        ${gaps.length ? `
          <div class="quiz-gaps">
            <h3>Что у вас пока не работает от модели</h3>
            <ul>${gaps.map((g) => `<li>${g}</li>`).join('')}</ul>
          </div>` : `
          <div class="quiz-gaps">
            <h3>Все четыре процесса уже завязаны на модель</h3>
            <p>Тогда разговор другой: где данные всё ещё расходятся с фактом и что автоматизировать следующим.</p>
          </div>`}
        <div class="quiz-cta">
          <h3>Напишите нам — разберём ваш случай</h3>
          <p>Расскажем, что из этого списка настраивается за пару недель, что требует перестройки процесса, и с чего дешевле начать именно вам. Без презентаций на сорок слайдов.</p>
          <form class="quiz-form" data-quiz-form>
            <input type="hidden" name="_subject" value="Заявка с теста «BIM на 100%»">
            <input type="hidden" name="_captcha" value="false">
            <input type="hidden" name="_template" value="table">
            <input type="hidden" name="result" value="${level.name} — ${percent}%">
            <input type="hidden" name="probely" value="${gaps.join('; ') || 'нет'}">
            <input type="text" name="_honey" class="quiz-honey" tabindex="-1" autocomplete="off" aria-hidden="true">
            <label class="quiz-field">
              <span>Как к вам обращаться</span>
              <input type="text" name="name" required placeholder="Имя и компания">
            </label>
            <label class="quiz-field">
              <span>Email или Telegram</span>
              <input type="text" name="contact" required placeholder="you@mail.ru или @username">
            </label>
            <label class="quiz-field">
              <span>Что болит сильнее всего <i>(необязательно)</i></span>
              <textarea name="task" rows="3" placeholder="Например: смета расходится с моделью на каждом изменении"></textarea>
            </label>
            <button class="btn" type="submit">Отправить и получить разбор</button>
            <p class="quiz-note" data-form-note>Ответим в течение рабочего дня. Или сразу в <a href="https://t.me/bim_pulse_ufa" target="_blank" rel="noopener">Telegram</a>, если так быстрее.</p>
          </form>
        </div>
        <button class="text-link quiz-restart" type="button" data-restart>Пройти заново</button>
      </div>`;

    bar.style.width = '100%';
    counter.textContent = 'Готово';

    animateNumber(stage.querySelector('[data-count]'), percent);
    requestAnimationFrame(() => {
      stage.querySelector('[data-scale]').style.width = `${percent}%`;
    });

    stage.querySelector('[data-restart]').addEventListener('click', () => {
      answers.length = 0;
      current = 0;
      renderQuestion();
      scrollToStage();
    });

    bindForm(stage.querySelector('[data-quiz-form]'));
  }

  function animateNumber(el, target) {
    const start = performance.now();
    const dur = 900;
    const step = (now) => {
      const p = Math.min((now - start) / dur, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  function bindForm(form) {
    if (!form) return;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const note = form.querySelector('[data-form-note]');
      const btn = form.querySelector('button[type="submit"]');
      if (form.querySelector('[name="_honey"]').value) return; // бот
      btn.disabled = true;
      btn.textContent = 'Отправляем…';

      const payload = {};
      new FormData(form).forEach((value, key) => { payload[key] = value; });

      try {
        const res = await fetch('https://formsubmit.co/ajax/bimaip@yandex.ru', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('bad status');
        goal('quiz_lead');
        form.innerHTML = `
          <div class="quiz-sent">
            <h4>Заявка ушла ✓</h4>
            <p>Вернёмся с разбором в течение рабочего дня. Если удобнее голосом или сразу с вопросами — <a href="https://t.me/bim_pulse_ufa" target="_blank" rel="noopener">пишите в Telegram</a>.</p>
          </div>`;
      } catch (error) {
        btn.disabled = false;
        btn.textContent = 'Отправить и получить разбор';
        note.innerHTML = 'Не отправилось — похоже, что-то с сетью. Напишите нам в <a href="https://t.me/bim_pulse_ufa" target="_blank" rel="noopener">Telegram</a> или на <a href="mailto:bimaip@yandex.ru">bimaip@yandex.ru</a>.';
      }
    });
  }

  startBtn.addEventListener('click', () => {
    if (!started) { started = true; goal('quiz_start'); }
    intro.hidden = true;
    quiz.querySelector('[data-progress]').hidden = false;
    renderQuestion();
    scrollToStage();
  });
})();
